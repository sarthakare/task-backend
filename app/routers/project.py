# app/routers/project.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio
import threading
from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.models.team import Team
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectTeamAdd
from app.utils.auth import get_current_user

router = APIRouter()

# WebSocket notification helper functions
async def send_project_notification(
    notification_type: str,
    title: str,
    message: str,
    target_user_ids: List[int] = None,
    project_data: dict = None
):
    """Send project-related WebSocket notification"""
    try:
        # Import here to avoid circular imports
        from main import send_toast, MessageTarget, send_to_user, broadcast_message, active_connections
        import json
        
        print(f"Sending project notification: {notification_type} to users {target_user_ids}")
        print(f"Active connections: {list(active_connections.keys())}")
        
        notification_data = {
            "type": "project_notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "project_data": project_data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        json_message = json.dumps(notification_data)
        
        if target_user_ids:
            # Send to specific users
            for user_id in target_user_ids:
                print(f"Attempting to send to user {user_id}")
                await send_to_user(user_id, json_message)
        else:
            print("Broadcasting to all users")
            await broadcast_message(json_message)
            
    except Exception as e:
        print(f"Error sending project notification: {e}")
        import traceback
        traceback.print_exc()

def send_project_notification_async(
    notification_type: str,
    title: str,
    message: str,
    target_user_ids: List[int] = None,
    project_data: dict = None
):
    """Helper function to send project notifications asynchronously from sync context"""
    def run_notification():
        try:
            # Ensure project_data is properly serialized
            if project_data:
                serialized_project_data = {}
                for key, value in project_data.items():
                    if hasattr(value, 'value'):  # Handle enums
                        serialized_project_data[key] = value.value
                    elif hasattr(value, 'isoformat'):  # Handle datetime
                        serialized_project_data[key] = value.isoformat()
                    else:
                        serialized_project_data[key] = value
            else:
                serialized_project_data = None
                
            asyncio.run(send_project_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                target_user_ids=target_user_ids,
                project_data=serialized_project_data
            ))
        except Exception as e:
            print(f"Error in project notification thread: {e}")
            import traceback
            traceback.print_exc()
    
    # Run in a separate thread to avoid blocking the main request
    thread = threading.Thread(target=run_notification, daemon=True)
    thread.start()

@router.get("/", response_model=List[ProjectOut])
def get_all_projects(db: Session = Depends(get_db)):
    """Get all projects with their managers and assigned teams"""
    projects = db.query(Project).all()
    return projects

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new project - Only admin and CEO can create projects"""
    
    # Check if user has permission to create projects
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can create projects"
        )
    
    # Check if project name already exists
    existing_project = db.query(Project).filter(Project.name == project_data.name).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    # Check if manager exists and is active
    manager = db.query(User).filter(User.id == project_data.manager_id).first()
    if not manager:
        raise HTTPException(status_code=400, detail="Project manager not found")
    if not manager.is_active:
        raise HTTPException(status_code=400, detail="Project manager is not active")
    
    # Check if all assigned teams exist and are active
    assigned_teams = []
    if project_data.assigned_teams:
        assigned_teams = db.query(Team).filter(Team.id.in_(project_data.assigned_teams)).all()
        if len(assigned_teams) != len(project_data.assigned_teams):
            raise HTTPException(status_code=400, detail="One or more assigned teams not found")
        
        inactive_teams = [team.name for team in assigned_teams if team.status != 'active']
        if inactive_teams:
            raise HTTPException(
                status_code=400, 
                detail=f"The following teams are inactive: {', '.join(inactive_teams)}"
            )
    
    # Validate date range
    if project_data.end_date <= project_data.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Validate status
    valid_statuses = ['active', 'on_hold', 'completed', 'cancelled']
    if project_data.status and project_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Create new project
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        manager_id=project_data.manager_id,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        status=project_data.status or "active"
    )
    
    # Add project to database
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Add assigned teams to project
    if assigned_teams:
        db_project.assigned_teams = assigned_teams
        db.commit()
        db.refresh(db_project)
    
    # Send WebSocket notification to all project team members
    try:
        # Create project data for notification
        project_data = {
            "project_id": db_project.id,
            "project_name": db_project.name,
            "description": db_project.description,
            "status": db_project.status,
            "start_date": db_project.start_date,
            "end_date": db_project.end_date,
            "manager_name": manager.name,
            "team_count": len(assigned_teams) if assigned_teams else 0,
            "created_by": current_user.name
        }
        
        # Get all team member IDs from assigned teams
        project_member_ids = []
        if assigned_teams:
            for team in assigned_teams:
                # Get all members from each team
                team_members = db.query(User).join(User.teams).filter(Team.id == team.id).all()
                project_member_ids.extend([member.id for member in team_members])
        
        # Add project manager to the list
        if manager.id not in project_member_ids:
            project_member_ids.append(manager.id)
        
        # Remove duplicates
        project_member_ids = list(set(project_member_ids))
        
        # Send notification to all project members
        send_project_notification_async(
            notification_type="project_created",
            title="New Project Created",
            message=f"You have been assigned to the new project '{db_project.name}' by {current_user.name}",
            target_user_ids=project_member_ids,
            project_data=project_data
        )
        
    except Exception as e:
        print(f"Error sending project creation notification: {e}")
        # Don't fail the main operation if notification fails
    
    return db_project

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a project - Only admin and CEO can edit projects"""
    
    # Check if user has permission to edit projects
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can edit projects"
        )
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project name already exists for another project
    if project_update.name and project_update.name != db_project.name:
        existing_project = db.query(Project).filter(
            Project.name == project_update.name,
            Project.id != project_id
        ).first()
        if existing_project:
            raise HTTPException(status_code=400, detail="Project name already exists")
    
    # Check if new manager exists and is active
    if project_update.manager_id and project_update.manager_id != db_project.manager_id:
        manager = db.query(User).filter(User.id == project_update.manager_id).first()
        if not manager:
            raise HTTPException(status_code=400, detail="Project manager not found")
        if not manager.is_active:
            raise HTTPException(status_code=400, detail="Project manager is not active")
    
    # Handle assigned teams updates
    if project_update.assigned_teams is not None:
        # Check if all teams exist and are active
        assigned_teams = db.query(Team).filter(Team.id.in_(project_update.assigned_teams)).all()
        if len(assigned_teams) != len(project_update.assigned_teams):
            raise HTTPException(status_code=400, detail="One or more assigned teams not found")
        
        inactive_teams = [team.name for team in assigned_teams if team.status != 'active']
        if inactive_teams:
            raise HTTPException(
                status_code=400, 
                detail=f"The following teams are inactive: {', '.join(inactive_teams)}"
            )
        
        # Update assigned teams
        db_project.assigned_teams = assigned_teams
    
    # Validate date range if dates are being updated
    start_date = project_update.start_date or db_project.start_date
    end_date = project_update.end_date or db_project.end_date
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Validate status
    if project_update.status:
        valid_statuses = ['active', 'on_hold', 'completed', 'cancelled']
        if project_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Update project fields
    update_data = project_update.model_dump(exclude_unset=True, exclude={'assigned_teams'})
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a project - Only admin and CEO can delete projects"""
    
    # Check if user has permission to delete projects
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can delete projects"
        )
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Remove all assigned teams from project before deleting
    db_project.assigned_teams.clear()
    db.delete(db_project)
    db.commit()
    return None

@router.get("/{project_id}/teams", response_model=List[dict])
def get_project_teams(project_id: int, db: Session = Depends(get_db)):
    """Get all teams assigned to a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return [
        {
            "id": team.id,
            "name": team.name,
            "department": team.department,
            "leader": team.leader.name,
            "member_count": len(team.members),
            "status": team.status
        }
        for team in project.assigned_teams
    ]

@router.post("/{project_id}/teams", response_model=dict)
def add_project_team(project_id: int, team_data: ProjectTeamAdd, db: Session = Depends(get_db)):
    """Add a team to a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team = db.query(Team).filter(Team.id == team_data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.status != 'active':
        raise HTTPException(status_code=400, detail="Team is not active")
    
    # Check if team is already assigned
    if team in project.assigned_teams:
        raise HTTPException(status_code=400, detail="Team is already assigned to this project")
    
    project.assigned_teams.append(team)
    db.commit()
    
    return {"message": f"Team {team.name} added to project {project.name}"}

@router.delete("/{project_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_team(project_id: int, team_id: int, db: Session = Depends(get_db)):
    """Remove a team from a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if team is assigned
    if team not in project.assigned_teams:
        raise HTTPException(status_code=400, detail="Team is not assigned to this project")
    
    project.assigned_teams.remove(team)
    db.commit()
    return None

@router.get("/stats/")
def get_project_stats(db: Session = Depends(get_db)):
    """Get project statistics"""
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()
    completed_projects = db.query(Project).filter(Project.status == "completed").count()
    on_hold_projects = db.query(Project).filter(Project.status == "on_hold").count()
    cancelled_projects = db.query(Project).filter(Project.status == "cancelled").count()
    
    # Count by manager (top project managers)
    manager_counts = {}
    managers = db.query(User).join(Project).all()
    for manager in managers:
        count = db.query(Project).filter(Project.manager_id == manager.id).count()
        if count > 0:
            manager_counts[manager.name] = count
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "on_hold_projects": on_hold_projects,
        "cancelled_projects": cancelled_projects,
        "manager_counts": manager_counts
    }
