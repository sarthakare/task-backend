# app/routers/notification.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.models import Notification, User, NotificationType, NotificationPriority
from app.schemas import (
    NotificationCreate, 
    NotificationUpdate, 
    NotificationOut, 
    NotificationSummary,
    NotificationStats,
    BulkNotificationUpdate,
    NotificationMarkAllRead
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationSummary])
def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    priority: Optional[NotificationPriority] = Query(None),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user with filtering options"""
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    # Apply filters
    if not include_archived:
        query = query.filter(Notification.is_archived == False)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    if priority:
        query = query.filter(Notification.priority == priority)
    
    # Filter out expired notifications
    query = query.filter(
        or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > datetime.utcnow()
        )
    )
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Notification.created_at))
    
    # Apply pagination
    notifications = query.offset(skip).limit(limit).all()
    
    return notifications

@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics for the current user"""
    
    # Base query for user's notifications
    base_query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    # Total count
    total_notifications = base_query.count()
    
    # Unread count
    unread_count = base_query.filter(Notification.is_read == False).count()
    
    # Read count
    read_count = base_query.filter(Notification.is_read == True).count()
    
    # Archived count
    archived_count = base_query.filter(Notification.is_archived == True).count()
    
    # Count by type
    type_counts = db.query(
        Notification.notification_type,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == current_user.id,
        Notification.is_archived == False
    ).group_by(Notification.notification_type).all()
    
    by_type = {str(ntype): count for ntype, count in type_counts}
    
    # Count by priority
    priority_counts = db.query(
        Notification.priority,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == current_user.id,
        Notification.is_archived == False
    ).group_by(Notification.priority).all()
    
    by_priority = {str(priority): count for priority, count in priority_counts}
    
    return NotificationStats(
        total_notifications=total_notifications,
        unread_count=unread_count,
        read_count=read_count,
        archived_count=archived_count,
        by_type=by_type,
        by_priority=by_priority
    )

@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification by ID"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification

@router.put("/{notification_id}", response_model=NotificationOut)
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific notification"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update fields
    update_data = notification_update.dict(exclude_unset=True)
    
    # Handle extra_data serialization
    if 'extra_data' in update_data and update_data['extra_data'] is not None:
        update_data['extra_data'] = json.dumps(update_data['extra_data'])
    
    # Set read_at timestamp if marking as read
    if update_data.get('is_read') == True and not notification.is_read:
        update_data['read_at'] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(notification, field, value)
    
    db.commit()
    db.refresh(notification)
    
    return notification

@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
    
    return notification

@router.put("/bulk/update", response_model=dict)
def bulk_update_notifications(
    bulk_update: BulkNotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update multiple notifications"""
    
    # Verify all notifications belong to the current user
    notifications = db.query(Notification).filter(
        Notification.id.in_(bulk_update.notification_ids),
        Notification.user_id == current_user.id
    ).all()
    
    if len(notifications) != len(bulk_update.notification_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some notifications not found or don't belong to current user"
        )
    
    # Update notifications
    update_data = bulk_update.dict(exclude_unset=True, exclude={'notification_ids'})
    
    # Set read_at timestamp if marking as read
    if update_data.get('is_read') == True:
        update_data['read_at'] = datetime.utcnow()
    
    for notification in notifications:
        for field, value in update_data.items():
            setattr(notification, field, value)
    
    db.commit()
    
    return {
        "message": f"Successfully updated {len(notifications)} notifications",
        "updated_count": len(notifications)
    }

@router.put("/mark-all-read", response_model=dict)
def mark_all_notifications_read(
    mark_all: NotificationMarkAllRead,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    
    if mark_all.notification_type:
        query = query.filter(Notification.notification_type == mark_all.notification_type)
    
    notifications = query.all()
    
    # Update all notifications
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Successfully marked {len(notifications)} notifications as read",
        "updated_count": len(notifications)
    }

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific notification"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}

@router.delete("/bulk/delete")
def bulk_delete_notifications(
    notification_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk delete multiple notifications"""
    
    # Verify all notifications belong to the current user
    notifications = db.query(Notification).filter(
        Notification.id.in_(notification_ids),
        Notification.user_id == current_user.id
    ).all()
    
    if len(notifications) != len(notification_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some notifications not found or don't belong to current user"
        )
    
    # Delete notifications
    for notification in notifications:
        db.delete(notification)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {len(notifications)} notifications",
        "deleted_count": len(notifications)
    }

# Admin endpoints for creating notifications
@router.post("/", response_model=NotificationOut)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification (admin/supervisor only)"""
    
    # Check if user has permission to create notifications
    if current_user.role not in ['ADMIN', 'CEO']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and CEOs can create notifications"
        )
    
    # Verify target user exists
    target_user = db.query(User).filter(User.id == notification.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )
    
    # Create notification
    notification_data = notification.dict()
    
    # Handle extra_data serialization
    if notification_data.get('extra_data'):
        notification_data['extra_data'] = json.dumps(notification_data['extra_data'])
    
    db_notification = Notification(**notification_data)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification
