from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import notification as notification_model
from app.models import user as user_model
from app.schemas import notification as notification_schema
from app.utils.auth import get_current_user
from app.services.websocket_manager import websocket_manager

router = APIRouter()

@router.get("/", response_model=notification_schema.NotificationList)
async def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    try:
        query = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id
        )
        
        if unread_only:
            query = query.filter(notification_model.Notification.is_read == False)
        
        # Get total count
        total = query.count()
        
        # Get notifications with pagination
        notifications = query.order_by(
            notification_model.Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Get unread count
        unread_count = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.is_read == False
        ).count()
        
        return {
            "notifications": notifications,
            "total": total,
            "unread_count": unread_count
        }
        
    except Exception as e:
        print(f"❌ Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")

@router.get("/{notification_id}", response_model=notification_schema.NotificationOut)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get a specific notification by ID"""
    try:
        notification = db.query(notification_model.Notification).filter(
            notification_model.Notification.id == notification_id,
            notification_model.Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notification")

@router.patch("/{notification_id}/read", response_model=notification_schema.NotificationOut)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        notification = db.query(notification_model.Notification).filter(
            notification_model.Notification.id == notification_id,
            notification_model.Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification.is_read = True
        notification.read_at = datetime.now()
        
        db.commit()
        db.refresh(notification)
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.patch("/read-all", response_model=dict)
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    try:
        updated_count = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.now()
        })
        
        db.commit()
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        print(f"❌ Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        notification = db.query(notification_model.Notification).filter(
            notification_model.Notification.id == notification_id,
            notification_model.Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

@router.get("/stats/summary", response_model=dict)
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get notification statistics for the current user"""
    try:
        total_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id
        ).count()
        
        unread_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.is_read == False
        ).count()
        
        # Get notifications by type
        assignment_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.type == "ASSIGNMENT"
        ).count()
        
        status_change_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.type == "STATUS_CHANGE"
        ).count()
        
        reminder_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.type == "REMINDER"
        ).count()
        
        escalation_notifications = db.query(notification_model.Notification).filter(
            notification_model.Notification.user_id == current_user.id,
            notification_model.Notification.type == "ESCALATION"
        ).count()
        
        return {
            "total": total_notifications,
            "unread": unread_notifications,
            "read": total_notifications - unread_notifications,
            "by_type": {
                "assignment": assignment_notifications,
                "status_change": status_change_notifications,
                "reminder": reminder_notifications,
                "escalation": escalation_notifications
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notification statistics")
