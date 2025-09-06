# app/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Task, Project, Team
from app.models.task import TaskStatus
from app.schemas.task import TaskOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard overview statistics"""
    
    # Get total counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == 'active').count()
    
    # Get task statistics
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.FINISHED).count()
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    
    # Get overdue tasks (tasks past due date and not finished/cancelled)
    now = datetime.utcnow()
    overdue_tasks = db.query(Task).filter(
        and_(
            Task.due_date < now,
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
        )
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks
    }

@router.get("/activities")
def get_recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activities (simplified version using recent tasks)"""
    
    # For now, we'll use recent task updates as activities
    # In a real application, you'd have a dedicated activities/audit log table
    recent_tasks = db.query(Task).order_by(Task.updated_at.desc()).limit(limit * 2).all()
    
    activities = []
    for task in recent_tasks:
        if task.updated_at:
            # Create activity based on task status
            if task.status == TaskStatus.FINISHED:
                action = f"completed task '{task.title}'"
            elif task.status == TaskStatus.IN_PROGRESS:
                action = f"started working on '{task.title}'"
            elif task.status == TaskStatus.PENDING:
                action = f"marked task '{task.title}' as pending"
            else:
                action = f"updated task '{task.title}'"
            
            activities.append({
                "id": f"task_{task.id}_{task.updated_at.timestamp()}",
                "user": {
                    "id": task.assignee.id,
                    "name": task.assignee.name,
                    "email": task.assignee.email
                },
                "action": action,
                "description": action,
                "created_at": task.updated_at.isoformat()
            })
    
    # Sort by created_at and limit
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    return activities[:limit]

@router.get("/deadlines", response_model=List[TaskOut])
def get_upcoming_deadlines(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks with upcoming deadlines"""
    
    # Calculate date range
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    # Get tasks due within the specified days that are not finished/cancelled
    upcoming_tasks = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(
        and_(
            Task.due_date >= now,
            Task.due_date <= end_date,
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
        )
    ).order_by(Task.due_date.asc()).limit(20).all()
    
    return upcoming_tasks

@router.get("/workload/{user_id}")
def get_user_workload(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload for a specific user"""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's tasks
    active_tasks = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(
        and_(
            Task.assigned_to == user_id,
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
        )
    ).all()
    
    # Calculate workload percentage (simple calculation based on number of tasks)
    # In a real application, you might consider task priority, estimated hours, etc.
    max_tasks = 10  # Assume 10 active tasks is 100% workload
    workload_percentage = min((len(active_tasks) / max_tasks) * 100, 100)
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "tasks": active_tasks,
        "workload_percentage": round(workload_percentage, 1)
    }

@router.get("/team-workload/{team_id}")
def get_team_workload(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload for a specific team"""
    
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get team members' workload
    members_workload = []
    for member in team.members:
        active_tasks = db.query(Task).options(
            joinedload(Task.creator),
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.team),
            joinedload(Task.task_logs)
        ).filter(
            and_(
                Task.assigned_to == member.id,
                ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
            )
        ).all()
        
        max_tasks = 10
        workload_percentage = min((len(active_tasks) / max_tasks) * 100, 100)
        
        members_workload.append({
            "user": {
                "id": member.id,
                "name": member.name,
                "email": member.email
            },
            "tasks": active_tasks,
            "workload_percentage": round(workload_percentage, 1)
        })
    
    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "department": team.department
        },
        "members_workload": members_workload
    }
