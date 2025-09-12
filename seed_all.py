"""
Master Database Seeding Script
Creates database tables and populates with demo data
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import demo data
from demo_users import DEMO_USERS
from demo_teams import DEMO_TEAMS
from demo_projects import DEMO_PROJECTS
from demo_tasks import DEMO_TASKS

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_session():
    """Create database session"""
    if "sqlite" in DATABASE_URL.lower():
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def run_create_tables():
    """Run create_tables.py script"""
    print(f"\n{'='*60}")
    print(f"🚀 Creating Database Tables")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, "create_tables.py"], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.getcwd())
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"[SUCCESS] Database tables created successfully!")
            return True
        else:
            print(f"[ERROR] Failed to create database tables with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error creating database tables: {e}")
        return False

def check_prerequisites():
    """Check if all required files exist"""
    required_files = [
        "create_tables.py",
        "demo_users.py",
        "demo_teams.py", 
        "demo_projects.py",
        "demo_tasks.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"[ERROR] Missing required files: {', '.join(missing_files)}")
        return False
    
    # Check if DATABASE_URL is set
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL environment variable not set!")
        return False
    
    return True

def seed_demo_users():
    """Create demo users in the database"""
    print(f"\n{'='*60}")
    print(f"🚀 Creating Demo Users")
    print(f"{'='*60}")
    
    try:
        from app.utils.security import get_password_hash
        session = get_db_session()
        created_users = []
        
        print("Creating demo users...")
        
        # First, get existing CEO user ID or create new CEO
        ceo_user = session.execute(
            text("SELECT id FROM users WHERE role = 'CEO'")
        ).fetchone()
        
        ceo_id = ceo_user[0] if ceo_user else None
        
        # Create users in hierarchical order
        id_mapping = {1: ceo_id}  # CEO is at index 1
        
        for i, user_data in enumerate(DEMO_USERS):
            # Check if user already exists
            existing_user = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]}
            ).fetchone()
            
            if existing_user:
                print(f"[SKIP] User {user_data['email']} already exists, skipping...")
                id_mapping[i + 1] = existing_user[0]
                continue
            
            # Hash password
            hashed_password = get_password_hash(user_data["password"])
            
            # Convert supervisor_id to actual database ID if it references a demo user
            actual_supervisor_id = user_data["supervisor_id"]
            if actual_supervisor_id and actual_supervisor_id in id_mapping:
                actual_supervisor_id = id_mapping[actual_supervisor_id]
            
            # Insert user into database
            result = session.execute(text("""
                INSERT INTO users (name, email, mobile, hashed_password, department, role, supervisor_id, is_active, created_at)
                VALUES (:name, :email, :mobile, :password, :department, :role, :supervisor_id, :is_active, NOW())
                RETURNING id
            """), {
                "name": user_data["name"],
                "email": user_data["email"],
                "mobile": user_data["mobile"],
                "password": hashed_password,
                "department": user_data["department"],
                "role": user_data["role"],
                "supervisor_id": actual_supervisor_id,
                "is_active": True
            })
            user_id = result.fetchone()[0]
            
            # Map this user's position to its actual database ID
            id_mapping[i + 1] = user_id
            
            created_users.append({
                "id": user_id,
                "name": user_data["name"],
                "email": user_data["email"],
                "role": user_data["role"],
                "department": user_data["department"]
            })
            
            print(f"[SUCCESS] Created user: {user_data['name']} ({user_data['role']} - {user_data['department']})")
        
        session.commit()
        print(f"\n[SUCCESS] Successfully created {len(created_users)} demo users!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating demo users: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def seed_demo_teams():
    """Create demo teams in the database"""
    print(f"\n{'='*60}")
    print(f"🚀 Creating Demo Teams")
    print(f"{'='*60}")
    
    try:
        session = get_db_session()
        created_teams = []
        
        print("Creating demo teams...")
        
        for team_data in DEMO_TEAMS:
            # Check if team already exists
            existing_team = session.execute(
                text("SELECT id FROM teams WHERE name = :name"),
                {"name": team_data["name"]}
            ).fetchone()
            
            if existing_team:
                print(f"[SKIP] Team {team_data['name']} already exists, skipping...")
                continue
            
            # Verify leader exists
            leader = session.execute(
                text("SELECT id FROM users WHERE id = :leader_id AND is_active = true"),
                {"leader_id": team_data["leader_id"]}
            ).fetchone()
            
            if not leader:
                print(f"[ERROR] Team leader with ID {team_data['leader_id']} not found or inactive, skipping team {team_data['name']}")
                continue
            
            # Create team
            result = session.execute(text("""
                INSERT INTO teams (name, description, department, leader_id, status, created_at, updated_at)
                VALUES (:name, :description, :department, :leader_id, :status, NOW(), NOW())
                RETURNING id
            """), {
                "name": team_data["name"],
                "description": team_data["description"],
                "department": team_data["department"],
                "leader_id": team_data["leader_id"],
                "status": team_data["status"]
            })
            team_id = result.fetchone()[0]
            
            # Add team members
            for member_id in team_data["member_ids"]:
                # Verify member exists and is active
                member = session.execute(
                    text("SELECT id FROM users WHERE id = :member_id AND is_active = true"),
                    {"member_id": member_id}
                ).fetchone()
                
                if member:
                    session.execute(text("""
                        INSERT INTO team_members (team_id, user_id)
                        VALUES (:team_id, :user_id)
                    """), {
                        "team_id": team_id,
                        "user_id": member_id
                    })
                else:
                    print(f"[SKIP] Member with ID {member_id} not found or inactive, skipping...")
            
            created_teams.append({
                "id": team_id,
                "name": team_data["name"],
                "department": team_data["department"],
                "leader_id": team_data["leader_id"],
                "member_count": len(team_data["member_ids"])
            })
            
            print(f"[SUCCESS] Created team: {team_data['name']} (Department: {team_data['department']}, Members: {len(team_data['member_ids'])})")
        
        session.commit()
        print(f"\n[SUCCESS] Successfully created {len(created_teams)} demo teams!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating demo teams: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def seed_demo_projects():
    """Create demo projects in the database"""
    print(f"\n{'='*60}")
    print(f"🚀 Creating Demo Projects")
    print(f"{'='*60}")
    
    try:
        session = get_db_session()
        created_projects = []
        
        print("Creating demo projects...")
        
        for project_data in DEMO_PROJECTS:
            # Check if project already exists
            existing_project = session.execute(
                text("SELECT id FROM projects WHERE name = :name"),
                {"name": project_data["name"]}
            ).fetchone()
            
            if existing_project:
                print(f"[SKIP] Project {project_data['name']} already exists, skipping...")
                continue
            
            # Verify manager exists and is active
            manager = session.execute(
                text("SELECT id FROM users WHERE id = :manager_id AND is_active = true"),
                {"manager_id": project_data["manager_id"]}
            ).fetchone()
            
            if not manager:
                print(f"[ERROR] Project manager with ID {project_data['manager_id']} not found or inactive, skipping project {project_data['name']}")
                continue
            
            # Create project
            result = session.execute(text("""
                INSERT INTO projects (name, description, manager_id, start_date, end_date, status, created_at, updated_at)
                VALUES (:name, :description, :manager_id, :start_date, :end_date, :status, NOW(), NOW())
                RETURNING id
            """), {
                "name": project_data["name"],
                "description": project_data["description"],
                "manager_id": project_data["manager_id"],
                "start_date": project_data["start_date"],
                "end_date": project_data["end_date"],
                "status": project_data["status"]
            })
            project_id = result.fetchone()[0]
            
            # Add assigned teams
            for team_id in project_data["assigned_teams"]:
                # Verify team exists
                team = session.execute(
                    text("SELECT id FROM teams WHERE id = :team_id"),
                    {"team_id": team_id}
                ).fetchone()
                
                if team:
                    session.execute(text("""
                        INSERT INTO project_teams (project_id, team_id)
                        VALUES (:project_id, :team_id)
                    """), {
                        "project_id": project_id,
                        "team_id": team_id
                    })
                else:
                    print(f"[SKIP] Team with ID {team_id} not found, skipping...")
            
            created_projects.append({
                "id": project_id,
                "name": project_data["name"],
                "manager_id": project_data["manager_id"],
                "status": project_data["status"],
                "team_count": len(project_data["assigned_teams"])
            })
            
            print(f"[SUCCESS] Created project: {project_data['name']} (Status: {project_data['status']}, Teams: {len(project_data['assigned_teams'])})")
        
        session.commit()
        print(f"\n[SUCCESS] Successfully created {len(created_projects)} demo projects!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating demo projects: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def seed_demo_tasks():
    """Create demo tasks in the database"""
    print(f"\n{'='*60}")
    print(f"🚀 Creating Demo Tasks")
    print(f"{'='*60}")
    
    try:
        from app.utils.security import get_password_hash
        session = get_db_session()
        created_tasks = []
        skipped_tasks = []
        
        print("Creating demo tasks...")
        
        # Get all active users for assignment
        all_users = session.execute(
            text("SELECT id, name, role, department FROM users WHERE is_active = true")
        ).fetchall()
        
        user_map = {user.id: user for user in all_users}
        
        for i, task_data in enumerate(DEMO_TASKS):
            # Check if task already exists
            existing_task = session.execute(
                text("SELECT id FROM tasks WHERE title = :title"),
                {"title": task_data["title"]}
            ).fetchone()
            
            if existing_task:
                print(f"[SKIP] Task '{task_data['title']}' already exists, skipping...")
                continue
            
            # Find a suitable creator based on the task's context
            creator_id = None
            assignee_id = task_data["assigned_to"]
            
            # If assignee exists in our user map, find a suitable creator
            if assignee_id in user_map:
                assignee = user_map[assignee_id]
                
                # Try to find a creator who can assign to this user (simplified hierarchy check)
                potential_creators = []
                for user_id, user in user_map.items():
                    # Simple hierarchy check: managers can assign to team leads and members
                    if (user.role == "manager" and assignee.role in ["team_lead", "member"]) or \
                       (user.role == "team_lead" and assignee.role == "member") or \
                       (user.role == assignee.role):  # Peers can assign to each other
                        potential_creators.append(user_id)
                
                if potential_creators:
                    # Prefer managers and team leads as creators
                    for creator_candidate in potential_creators:
                        creator_role = user_map[creator_candidate].role
                        if creator_role in ["manager", "team_lead"]:
                            creator_id = creator_candidate
                            break
                    
                    # If no manager/team lead found, use any valid creator
                    if not creator_id:
                        creator_id = potential_creators[0]
                else:
                    # If no valid creator found, skip this task
                    skipped_tasks.append({
                        "title": task_data["title"],
                        "reason": f"No valid creator found for assignee {assignee.name}"
                    })
                    continue
            else:
                # If assignee doesn't exist, skip this task
                skipped_tasks.append({
                    "title": task_data["title"],
                    "reason": f"Assignee with ID {assignee_id} not found"
                })
                continue
            
            # Verify project exists if specified
            project_id = task_data.get("project_id")
            if project_id:
                project = session.execute(
                    text("SELECT id FROM projects WHERE id = :project_id"),
                    {"project_id": project_id}
                ).fetchone()
                if not project:
                    project_id = None  # Remove invalid project reference
            
            # Verify team exists if specified
            team_id = task_data.get("team_id")
            if team_id:
                team = session.execute(
                    text("SELECT id FROM teams WHERE id = :team_id"),
                    {"team_id": team_id}
                ).fetchone()
                if not team:
                    team_id = None  # Remove invalid team reference
            
            # Create task
            result = session.execute(text("""
                INSERT INTO tasks (title, description, created_by, assigned_to, project_id, team_id, 
                                 status, priority, start_date, due_date, follow_up_date, created_at, updated_at)
                VALUES (:title, :description, :created_by, :assigned_to, :project_id, :team_id,
                        :status, :priority, :start_date, :due_date, :follow_up_date, NOW(), NOW())
                RETURNING id
            """), {
                "title": task_data["title"],
                "description": task_data["description"],
                "created_by": creator_id,
                "assigned_to": assignee_id,
                "project_id": project_id,
                "team_id": team_id,
                "status": task_data["status"].value if hasattr(task_data["status"], 'value') else str(task_data["status"]),
                "priority": task_data["priority"].value if hasattr(task_data["priority"], 'value') else str(task_data["priority"]),
                "start_date": task_data["start_date"],
                "due_date": task_data["due_date"],
                "follow_up_date": task_data["follow_up_date"]
            })
            task_id = result.fetchone()[0]
            
            created_tasks.append({
                "id": task_id,
                "title": task_data["title"],
                "creator_id": creator_id,
                "assignee_id": assignee_id,
                "status": task_data["status"],
                "priority": task_data["priority"]
            })
            
            creator_name = user_map[creator_id].name if creator_id in user_map else "Unknown"
            assignee_name = user_map[assignee_id].name if assignee_id in user_map else "Unknown"
            
            print(f"[SUCCESS] Created task: {task_data['title']} (Creator: {creator_name} -> Assignee: {assignee_name})")
        
        session.commit()
        print(f"\n[SUCCESS] Successfully created {len(created_tasks)} demo tasks!")
        
        if skipped_tasks:
            print(f"\n[SKIP] Skipped {len(skipped_tasks)} tasks:")
            for task in skipped_tasks:
                print(f"   - {task['title']}: {task['reason']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating demo tasks: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Main function to run all seeding operations"""
    print("🌱 MASTER DATABASE SEEDING SCRIPT")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n[ERROR] Prerequisites check failed!")
        sys.exit(1)
    
    print("[SUCCESS] Prerequisites check passed!")
    
    # Define the seeding order
    seeding_operations = [
        ("run_create_tables", "Creating Database Tables"),
        ("seed_demo_users", "Creating Demo Users"),
        ("seed_demo_teams", "Creating Demo Teams"), 
        ("seed_demo_projects", "Creating Demo Projects"),
        ("seed_demo_tasks", "Creating Demo Tasks")
    ]
    
    success_count = 0
    failed_operations = []
    
    # Run each seeding operation
    for operation, description in seeding_operations:
        if operation == "run_create_tables":
            success = run_create_tables()
        elif operation == "seed_demo_users":
            success = seed_demo_users()
        elif operation == "seed_demo_teams":
            success = seed_demo_teams()
        elif operation == "seed_demo_projects":
            success = seed_demo_projects()
        elif operation == "seed_demo_tasks":
            success = seed_demo_tasks()
        
        if success:
            success_count += 1
        else:
            failed_operations.append(operation)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SEEDING SUMMARY")
    print(f"{'='*60}")
    print(f"Total Operations: {len(seeding_operations)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_operations)}")
    
    if failed_operations:
        print(f"Failed Operations: {', '.join(failed_operations)}")
    
    if success_count == len(seeding_operations):
        print(f"\n[SUCCESS] ALL SEEDING OPERATIONS COMPLETED SUCCESSFULLY!")
        print(f"Your database is now fully populated with demo data.")
        print(f"\n[INFO] What was created:")
        print(f"   - Database tables and schema")
        print(f"   - 31 Users (CEO, 7 Managers, 9 Team Leads, 14 Members)")
        print(f"   - 9 Teams across 7 departments")
        print(f"   - 17 Projects (15 active, 2 completed)")
        print(f"   - 24+ Tasks with proper hierarchy constraints")
        print(f"\n[INFO] Login Credentials:")
        print(f"   - Admin: admin@example.com / admin123")
        print(f"   - CEO: ceo@test.com / password123")
        print(f"   - All other users: password123")
    else:
        print(f"\n[WARNING] Some seeding operations failed. Please check the errors above.")
        sys.exit(1)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
