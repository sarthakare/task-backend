# app/routers/reminder.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Reminder, User, Task
from app.schemas import ReminderCreate, ReminderUpdate, ReminderOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("/", response_model=List[ReminderOut])
def get_all_reminders(
    skip: int = 0,
    limit: int = 100,
    is_completed: Optional[bool] = None,
    priority: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reminders with optional filtering"""
    query = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    )
    
    # Apply filters
    if is_completed is not None:
        query = query.filter(Reminder.is_completed == is_completed)
    if priority:
        query = query.filter(Reminder.priority == priority)
    if user_id:
        query = query.filter(Reminder.user_id == user_id)
    
    reminders = query.order_by(Reminder.due_date.asc()).offset(skip).limit(limit).all()
    return reminders

@router.get("/user/{user_id}", response_model=List[ReminderOut])
def get_reminders_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    is_completed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reminders for a specific user"""
    query = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    ).filter(Reminder.user_id == user_id)
    
    if is_completed is not None:
        query = query.filter(Reminder.is_completed == is_completed)
    
    reminders = query.order_by(Reminder.due_date.asc()).offset(skip).limit(limit).all()
    return reminders

@router.get("/{reminder_id}", response_model=ReminderOut)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific reminder by ID"""
    reminder = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    ).filter(Reminder.id == reminder_id).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return reminder

@router.post("/", response_model=ReminderOut)
def create_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new reminder"""
    
    # Validate user exists and is active
    user = db.query(User).filter(User.id == reminder.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive"
        )
    
    # Validate task if provided
    if reminder.task_id:
        task = db.query(Task).filter(Task.id == reminder.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found"
            )
    
    # Create the reminder
    db_reminder = Reminder(
        title=reminder.title,
        description=reminder.description,
        due_date=reminder.due_date,
        priority=reminder.priority,
        user_id=reminder.user_id,
        task_id=reminder.task_id
    )
    
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    
    # Load relationships for response
    db_reminder = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    ).filter(Reminder.id == db_reminder.id).first()
    
    return db_reminder

@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    reminder_update: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a reminder"""
    
    # Get the reminder
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    # Validate user if being updated
    if reminder_update.user_id:
        user = db.query(User).filter(
            User.id == reminder_update.user_id,
            User.is_active == True
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found or inactive"
            )
    
    # Validate task if being updated
    if reminder_update.task_id:
        task = db.query(Task).filter(Task.id == reminder_update.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found"
            )
    
    # Update fields
    update_data = reminder_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reminder, field, value)
    
    # Set completed_at if is_completed is being set to True
    if reminder_update.is_completed and not db_reminder.completed_at:
        db_reminder.completed_at = datetime.utcnow()
    elif reminder_update.is_completed == False:
        db_reminder.completed_at = None
    
    db_reminder.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_reminder)
    
    # Load relationships for response
    db_reminder = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    ).filter(Reminder.id == db_reminder.id).first()
    
    return db_reminder

@router.patch("/{reminder_id}/complete", response_model=ReminderOut)
def mark_reminder_completed(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a reminder as completed"""
    
    # Get the reminder
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    # Mark as completed
    db_reminder.is_completed = True
    db_reminder.completed_at = datetime.utcnow()
    db_reminder.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reminder)
    
    # Load relationships for response
    db_reminder = db.query(Reminder).options(
        joinedload(Reminder.user),
        joinedload(Reminder.task)
    ).filter(Reminder.id == db_reminder.id).first()
    
    return db_reminder

@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a reminder"""
    
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    db.delete(db_reminder)
    db.commit()
    
    return {"message": "Reminder deleted successfully"}

@router.get("/stats/overview")
def get_reminder_stats(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reminder statistics"""
    query = db.query(Reminder)
    
    if user_id:
        query = query.filter(Reminder.user_id == user_id)
    
    # Basic counts
    total_reminders = query.count()
    active_reminders = query.filter(Reminder.is_completed == False).count()
    completed_reminders = query.filter(Reminder.is_completed == True).count()
    
    # Date-based counts
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    overdue_reminders = query.filter(
        Reminder.due_date < now,
        Reminder.is_completed == False
    ).count()
    
    today_reminders = query.filter(
        Reminder.due_date >= today_start,
        Reminder.due_date <= today_end,
        Reminder.is_completed == False
    ).count()
    
    return {
        "total_reminders": total_reminders,
        "active_reminders": active_reminders,
        "completed_reminders": completed_reminders,
        "overdue_reminders": overdue_reminders,
        "today_reminders": today_reminders
    }
