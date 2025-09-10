# create_tables.py
from sqlalchemy import create_engine, text
from app.database import Base
from app.models.user import User
from app.models.team import Team
from app.models.project import Project
from app.models.task import Task, TaskLog
from app.models.reminder import Reminder
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

def create_tables():
    """Create all tables"""
    try:
        # Drop existing tables if they exist (in correct order due to foreign keys)
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS reminders CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS task_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS tasks CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS project_teams CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS team_members CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS teams CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Create default admin user
        create_default_admin()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

def create_default_admin():
    """Create a default admin user"""
    try:
        from app.utils.security import get_password_hash
        
        with engine.connect() as conn:
            # Hash password
            admin_password = get_password_hash("admin123")
            
            # Check if admin user already exists
            admin_exists = conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'")).scalar()
            
            # Create admin user if doesn't exist
            if admin_exists == 0:
                if "postgresql" in DATABASE_URL.lower():
                    conn.execute(text("""
                        INSERT INTO users (name, email, mobile, hashed_password, department, role, supervisor_id, is_active, created_at)
                        VALUES (:name, :email, :mobile, :password, :department, :role, :supervisor_id, :is_active, NOW())
                    """), {
                        "name": "System Administrator",
                        "email": "admin@example.com",
                        "mobile": "+1-555-0000",
                        "password": admin_password,
                        "department": "IT",
                        "role": "ADMIN",
                        "supervisor_id": None,
                        "is_active": True
                    })
                else:
                    # SQLite syntax
                    conn.execute(text("""
                        INSERT INTO users (name, email, mobile, hashed_password, department, role, supervisor_id, is_active, created_at)
                        VALUES (:name, :email, :mobile, :password, :department, :role, :supervisor_id, :is_active, datetime('now'))
                    """), {
                        "name": "System Administrator",
                        "email": "admin@example.com",
                        "mobile": "+1-555-0000",
                        "password": admin_password,
                        "department": "IT",
                        "role": "ADMIN",
                        "supervisor_id": None,
                        "is_active": True
                    })
                
                conn.commit()
                print("✅ Default admin user created!")
                print("   Email: admin@example.com")
                print("   Password: admin123")
            else:
                print("ℹ️  Admin user already exists")
            
    except Exception as e:
        print(f"❌ Error creating default admin: {e}")

if __name__ == "__main__":
    create_tables()
