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
from app.utils.hierarchy import HierarchyManager

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get personalized dashboard overview statistics based on user role and hierarchy"""
    
    hierarchy_manager = HierarchyManager(db)
    
    # Get viewable user IDs based on user's role and hierarchy
    viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
    
    # Get user's role for personalized messaging
    user_role = current_user.role.upper()
    
    # Get total counts based on user's scope
    if user_role in ['ADMIN', 'CEO']:
        # Admin and CEO see all data
        total_users = db.query(User).filter(User.role != "ADMIN").count()
        active_users = db.query(User).filter(
            User.is_active == True,
            User.role != "ADMIN"
        ).count()
        total_projects = db.query(Project).count()
        active_projects = db.query(Project).filter(Project.status == 'active').count()
    else:
        # Other roles see only their scope
        total_users = db.query(User).filter(User.id.in_(viewable_user_ids)).count()
        active_users = db.query(User).filter(
            User.id.in_(viewable_user_ids),
            User.is_active == True
        ).count()
        
        # For projects, show only projects where user is manager or team is assigned
        # Get projects where user is the manager
        user_managed_projects = db.query(Project).filter(Project.manager_id == current_user.id)
        
        # Get projects where user's teams are assigned
        user_teams = db.query(Team).filter(Team.leader_id == current_user.id).all()
        team_member_projects = []
        for team in user_teams:
            team_projects = db.query(Project).join(Project.assigned_teams).filter(
                Project.assigned_teams.any(Team.id == team.id)
            ).all()
            team_member_projects.extend(team_projects)
        
        # Get projects where user is a team member
        user_team_memberships = db.query(Team).join(Team.members).filter(
            Team.members.any(User.id == current_user.id)
        ).all()
        for team in user_team_memberships:
            member_projects = db.query(Project).join(Project.assigned_teams).filter(
                Project.assigned_teams.any(Team.id == team.id)
            ).all()
            team_member_projects.extend(member_projects)
        
        # Combine all relevant projects
        all_user_projects = list(user_managed_projects) + team_member_projects
        unique_project_ids = list(set([p.id for p in all_user_projects]))
        
        if unique_project_ids:
            total_projects = len(unique_project_ids)
            active_projects = db.query(Project).filter(
                Project.id.in_(unique_project_ids),
                Project.status == 'active'
            ).count()
        else:
            total_projects = 0
            active_projects = 0
    
    # Get task statistics based on user's scope
    # Tasks created by or assigned to viewable users
    task_query = db.query(Task).filter(
        or_(
            Task.created_by.in_(viewable_user_ids),
            Task.assigned_to.in_(viewable_user_ids)
        )
    )
    
    total_tasks = task_query.count()
    completed_tasks = task_query.filter(Task.status == TaskStatus.FINISHED).count()
    pending_tasks = task_query.filter(Task.status == TaskStatus.PENDING).count()
    
    # Get overdue tasks (tasks past due date and not finished/cancelled)
    now = datetime.utcnow()
    overdue_tasks = task_query.filter(
        and_(
            Task.due_date < now,
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
        )
    ).count()
    
    # Get user's direct subordinates count for managers/team leads
    direct_subordinates_count = 0
    if user_role in ['MANAGER', 'TEAM_LEAD']:
        direct_subordinates_count = len(hierarchy_manager.get_direct_subordinates(current_user.id))
    
    # Get comprehensive scope information
    scope_info = hierarchy_manager.get_access_scope_info(current_user.id)
    
    # Get team information if user is a team lead
    team_info = None
    if user_role == 'TEAM_LEAD':
        teams_leading = db.query(Team).filter(Team.leader_id == current_user.id).all()
        if teams_leading:
            team_info = {
                "team_name": teams_leading[0].name,
                "department": teams_leading[0].department,
                "member_count": len(teams_leading[0].members)
            }
    
    # Get additional scope details
    scope_details = {
        "total_teams_leading": 0,
        "total_teams_member": 0,
        "total_direct_reports": direct_subordinates_count,
        "total_subordinates": 0,
        "department_info": None
    }
    
    if user_role in ['MANAGER', 'TEAM_LEAD']:
        # Count teams they are leading
        scope_details["total_teams_leading"] = db.query(Team).filter(Team.leader_id == current_user.id).count()
        
        # Count teams they are members of
        scope_details["total_teams_member"] = db.query(Team).join(Team.members).filter(
            Team.members.any(User.id == current_user.id)
        ).count()
        
        # Count total subordinates (direct + indirect)
        all_subordinates = hierarchy_manager.get_all_subordinates(current_user.id)
        scope_details["total_subordinates"] = len(all_subordinates)
    
    # Get department information
    if current_user.department:
        department_users = db.query(User).filter(
            User.department == current_user.department,
            User.is_active == True
        ).count()
        scope_details["department_info"] = {
            "department": current_user.department,
            "total_members": department_users
        }
    
    return {
        "user_role": user_role,
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "direct_subordinates_count": direct_subordinates_count,
        "team_info": team_info,
        "scope_description": scope_info,
        "scope_details": scope_details
    }

@router.get("/activities")
def get_recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activities based on user's role and hierarchy scope"""
    
    hierarchy_manager = HierarchyManager(db)
    viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
    
    # Get recent tasks within user's scope
    recent_tasks = db.query(Task).filter(
        or_(
            Task.created_by.in_(viewable_user_ids),
            Task.assigned_to.in_(viewable_user_ids)
        )
    ).order_by(Task.updated_at.desc()).limit(limit * 2).all()
    
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
    """Get tasks with upcoming deadlines based on user's role and hierarchy scope"""
    
    hierarchy_manager = HierarchyManager(db)
    viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
    
    # Calculate date range
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    # Get tasks due within the specified days that are not finished/cancelled
    # and within user's scope
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
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED]),
            or_(
                Task.created_by.in_(viewable_user_ids),
                Task.assigned_to.in_(viewable_user_ids)
            )
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

@router.get("/projects")
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get projects based on user's role and hierarchy scope"""
    
    hierarchy_manager = HierarchyManager(db)
    user_role = current_user.role.upper()
    
    if user_role in ['ADMIN', 'CEO']:
        # Admin and CEO see all projects
        projects = db.query(Project).options(
            joinedload(Project.manager),
            joinedload(Project.assigned_teams)
        ).all()
    else:
        # Other roles see only their assigned projects
        # Get projects where user is the manager
        user_managed_projects = db.query(Project).filter(Project.manager_id == current_user.id)
        
        # Get projects where user's teams are assigned
        user_teams = db.query(Team).filter(Team.leader_id == current_user.id).all()
        team_member_projects = []
        for team in user_teams:
            team_projects = db.query(Project).join(Project.assigned_teams).filter(
                Project.assigned_teams.any(Team.id == team.id)
            ).all()
            team_member_projects.extend(team_projects)
        
        # Get projects where user is a team member
        user_team_memberships = db.query(Team).join(Team.members).filter(
            Team.members.any(User.id == current_user.id)
        ).all()
        for team in user_team_memberships:
            member_projects = db.query(Project).join(Project.assigned_teams).filter(
                Project.assigned_teams.any(Team.id == team.id)
            ).all()
            team_member_projects.extend(member_projects)
        
        # Combine all relevant projects
        all_user_projects = list(user_managed_projects) + team_member_projects
        unique_project_ids = list(set([p.id for p in all_user_projects]))
        
        if unique_project_ids:
            projects = db.query(Project).options(
                joinedload(Project.manager),
                joinedload(Project.assigned_teams)
            ).filter(Project.id.in_(unique_project_ids)).all()
        else:
            projects = []
    
    return projects
