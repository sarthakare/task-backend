# app/routers/task.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Task, TaskLog, User, Project, Team, TaskStatus as TaskStatusEnum
from app.schemas import TaskCreate, TaskUpdate, TaskOut, TaskLogCreate, TaskLogOut
from app.utils.auth import get_current_user
from app.utils.hierarchy import HierarchyManager

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskOut])
def get_all_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    show_all: bool = False,  # Admin/supervisor override
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks with role-based access control
    
    Role-based task visibility:
    - ADMIN and CEO: see all tasks
    - MANAGER: see own + team_lead + member tasks
    - TEAM_LEAD: see own + member tasks  
    - MEMBER: see only own tasks
    """
    hierarchy_manager = HierarchyManager(db)
    
    query = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    )
    
    # Apply role-based filtering
    role = current_user.role.upper()
    
    if role in ['ADMIN', 'CEO']:
        # ADMIN and CEO can see all tasks - no filtering needed
        pass
    else:
        # Get user IDs that current user can view based on role
        viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
        
        # Filter tasks that user can view based on role scope
        query = query.filter(
            or_(
                Task.created_by.in_(viewable_user_ids),
                Task.assigned_to.in_(viewable_user_ids)
            )
        )
    
    # Apply additional filters
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if team_id:
        query = query.filter(Task.team_id == team_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # Additional security check for non-admin/ceo users
    if role not in ['ADMIN', 'CEO']:
        accessible_tasks = []
        for task in tasks:
            if hierarchy_manager.can_view_task_by_role(current_user.id, task.created_by, task.assigned_to):
                accessible_tasks.append(task)
        return accessible_tasks
    
    return tasks

@router.get("/access-scope", response_model=dict)
def get_access_scope(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get information about current user's task access scope based on role"""
    hierarchy_manager = HierarchyManager(db)
    return hierarchy_manager.get_access_scope_info(current_user.id)

@router.get("/{task_id}/can-edit", response_model=dict)
def can_edit_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if current user can edit a specific task"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can modify this task
    can_edit = hierarchy_manager.can_modify_task(current_user.id, task.created_by, task.assigned_to)
    
    return {
        "can_edit": can_edit,
        "user_id": current_user.id,
        "user_role": current_user.role,
        "task_id": task_id
    }

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task by ID with role-based access control"""
    hierarchy_manager = HierarchyManager(db)
    
    task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can view this task based on role-based scope
    if not hierarchy_manager.can_view_task_by_role(current_user.id, task.created_by, task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this task"
        )
    
    return task

@router.post("/", response_model=TaskOut)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task with hierarchy-based assignment validation"""
    hierarchy_manager = HierarchyManager(db)
    
    # Validate assignee exists and is active
    assignee = db.query(User).filter(User.id == task.assigned_to, User.is_active == True).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user not found or inactive"
        )
    
    # Validate assignment is allowed based on hierarchy
    if not hierarchy_manager.is_peer_or_subordinate(current_user.id, task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign tasks to your subordinates or peers. Cannot assign tasks to superiors."
        )
    
    # Validate project if provided
    if task.project_id:
        project = db.query(Project).filter(
            Project.id == task.project_id,
            Project.status.in_(["active"])
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or not active"
            )
    
    # Validate team if provided
    if task.team_id:
        team = db.query(Team).filter(
            Team.id == task.team_id,
            Team.status == "active"
        ).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found or not active"
            )
    
    # Create the task
    db_task = Task(
        title=task.title,
        description=task.description,
        created_by=current_user.id,
        assigned_to=task.assigned_to,
        project_id=task.project_id,
        team_id=task.team_id,
        status=task.status,
        priority=task.priority,
        start_date=task.start_date,
        due_date=task.due_date,
        follow_up_date=task.follow_up_date
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    return db_task

@router.put("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update only the status of a task with more permissive access control"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can update status of this task
    if not hierarchy_manager.can_update_task_status(current_user.id, db_task.created_by, db_task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task's status"
        )
    
    # Validate status
    new_status = status_update.get('status')
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status value
    valid_statuses = [status.value for status in TaskStatusEnum]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update only the status
    db_task.status = new_status
    
    # Set completed_at if status is FINISHED
    if new_status == TaskStatusEnum.FINISHED and db_task.completed_at is None:
        db_task.completed_at = datetime.utcnow()
    elif new_status != TaskStatusEnum.FINISHED:
        db_task.completed_at = None
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    return db_task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a task with hierarchy-based access control"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can modify this task
    if not hierarchy_manager.can_modify_task(current_user.id, db_task.created_by, db_task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this task"
        )
    
    # Validate assignee if being updated
    if task_update.assigned_to:
        assignee = db.query(User).filter(
            User.id == task_update.assigned_to,
            User.is_active == True
        ).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not found or inactive"
            )
        
        # Validate assignment is allowed based on hierarchy
        if not hierarchy_manager.is_peer_or_subordinate(current_user.id, task_update.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign tasks to your subordinates or peers. Cannot assign tasks to superiors."
            )
    
    # Validate project if being updated
    if task_update.project_id:
        project = db.query(Project).filter(
            Project.id == task_update.project_id,
            Project.status.in_(["active"])
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or not active"
            )
    
    # Validate team if being updated
    if task_update.team_id:
        team = db.query(Team).filter(
            Team.id == task_update.team_id,
            Team.status == "active"
        ).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found or not active"
            )
    
    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Set completed_at if status is FINISHED
    if task_update.status == TaskStatusEnum.FINISHED and db_task.completed_at is None:
        db_task.completed_at = datetime.utcnow()
    elif task_update.status != TaskStatusEnum.FINISHED:
        db_task.completed_at = None
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    return db_task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Only allow creator or assigned user to delete
    if db_task.created_by != current_user.id and db_task.assigned_to != current_user.id:
        # You might want to add role-based permissions here
        pass
    
    db.delete(db_task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

# Task Log endpoints
@router.post("/{task_id}/logs", response_model=TaskLogOut)
def create_task_log(
    task_id: int,
    log: TaskLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a log entry for a task"""
    
    # Verify task exists
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Create log entry
    db_log = TaskLog(
        task_id=task_id,
        title=log.title,
        description=log.description,
        start_time=log.start_time,
        end_time=log.end_time
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log

@router.get("/{task_id}/logs", response_model=List[TaskLogOut])
def get_task_logs(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all log entries for a task"""
    
    # Verify task exists
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.desc()).all()
    return logs

# New hierarchy-based endpoints
@router.get("/assignable-users", response_model=List[dict])
def get_assignable_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users that can be assigned tasks by the current user"""
    hierarchy_manager = HierarchyManager(db)
    assignable_users = hierarchy_manager.get_assignable_users(current_user.id)
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "is_subordinate": hierarchy_manager.is_subordinate_of(user.id, current_user.id),
            "is_peer": (user.supervisor_id == current_user.supervisor_id and 
                       user.id != current_user.id and current_user.supervisor_id is not None)
        }
        for user in assignable_users
    ]

@router.get("/my-team-tasks", response_model=List[TaskOut])
def get_my_team_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks for current user's scope based on role"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get user IDs that current user can view based on role
    viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
    
    tasks = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(
        or_(
            Task.created_by.in_(viewable_user_ids),
            Task.assigned_to.in_(viewable_user_ids)
        )
    ).offset(skip).limit(limit).all()
    
    return tasks
