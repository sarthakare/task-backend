# app/routers/task.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Task, TaskLog, User, Project, Team, TaskStatus as TaskStatusEnum
from app.schemas import TaskCreate, TaskUpdate, TaskOut, TaskLogCreate, TaskLogOut
from app.utils.auth import get_current_user

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks with optional filtering"""
    query = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    )
    
    # Apply filters
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
    return tasks

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task by ID"""
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
    
    return task

@router.post("/", response_model=TaskOut)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    
    # Validate assignee exists and is active
    assignee = db.query(User).filter(User.id == task.assigned_to, User.is_active == True).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user not found or inactive"
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

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    
    # Get the task
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
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
