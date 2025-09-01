from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from app.models import notification as notification_model
from app.models import user as user_model
from app.models import tasks as task_model
from app.schemas import notification as notification_schema
from app.services.websocket_manager import websocket_manager

class NotificationService:
    @staticmethod
    async def create_notification(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        task_id: Optional[int] = None
    ) -> notification_model.Notification:
        """Create a notification and send it via WebSocket if user is connected"""
        try:
            # Create notification in database
            notification = notification_model.Notification(
                user_id=user_id,
                task_id=task_id,
                type=notification_type,
                title=title,
                message=message,
                is_read=False
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send real-time notification if user is connected
            await websocket_manager.send_notification_to_user(
                user_id=user_id,
                notification=notification_schema.NotificationOut.model_validate(notification).model_dump()
            )
            
            print(f"✅ Notification created and sent to user {user_id}: {title}")
            return notification
            
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def create_task_assignment_notification(
        db: Session,
        task: task_model.Task,
        assigned_user: user_model.User,
        creator_user: user_model.User
    ) -> notification_model.Notification:
        """Create a notification when a task is assigned to a user"""
        title = "New Task Assigned"
        message = f"You have been assigned a new task: '{task.title}' by {creator_user.name}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=assigned_user.id,
            notification_type="ASSIGNMENT",
            title=title,
            message=message,
            task_id=task.id
        )
    
    @staticmethod
    async def create_task_status_change_notification(
        db: Session,
        task: task_model.Task,
        old_status: str,
        new_status: str,
        updated_by: user_model.User
    ) -> notification_model.Notification:
        """Create a notification when task status changes"""
        title = "Task Status Updated"
        message = f"Task '{task.title}' status changed from {old_status} to {new_status} by {updated_by.name}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=task.created_by,  # Notify the task creator
            notification_type="STATUS_CHANGE",
            title=title,
            message=message,
            task_id=task.id
        )
    
    @staticmethod
    async def create_task_reminder_notification(
        db: Session,
        task: task_model.Task,
        user: user_model.User
    ) -> notification_model.Notification:
        """Create a reminder notification for a task"""
        title = "Task Reminder"
        message = f"Reminder: Task '{task.title}' is due on {task.due_date.strftime('%Y-%m-%d %H:%M')}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user.id,
            notification_type="REMINDER",
            title=title,
            message=message,
            task_id=task.id
        )
    
    @staticmethod
    async def create_task_escalation_notification(
        db: Session,
        task: task_model.Task,
        escalated_to: user_model.User,
        reason: str
    ) -> notification_model.Notification:
        """Create an escalation notification for a task"""
        title = "Task Escalation"
        message = f"Task '{task.title}' has been escalated to you. Reason: {reason}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=escalated_to.id,
            notification_type="ESCALATION",
            title=title,
            message=message,
            task_id=task.id
        )
    
    @staticmethod
    async def create_general_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str
    ) -> notification_model.Notification:
        """Create a general notification (not related to a specific task)"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="GENERAL",
            title=title,
            message=message
        )
    
    @staticmethod
    async def broadcast_notification_to_all_users(
        db: Session,
        title: str,
        message: str,
        notification_type: str = "BROADCAST"
    ) -> None:
        """Broadcast a notification to all users"""
        try:
            # Get all users
            users = db.query(user_model.User).all()
            
            # Create notifications for all users
            for user in users:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user.id,
                    notification_type=notification_type,
                    title=title,
                    message=message
                )
            
            print(f"✅ Broadcast notification sent to {len(users)} users: {title}")
            
        except Exception as e:
            print(f"❌ Error broadcasting notification: {e}")
            raise
    
    @staticmethod
    async def send_notification_to_multiple_users(
        db: Session,
        user_ids: list[int],
        title: str,
        message: str,
        notification_type: str = "GENERAL",
        task_id: Optional[int] = None
    ) -> list[notification_model.Notification]:
        """Send the same notification to multiple users"""
        notifications = []
        
        for user_id in user_ids:
            try:
                notification = await NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    task_id=task_id
                )
                notifications.append(notification)
            except Exception as e:
                print(f"❌ Error sending notification to user {user_id}: {e}")
                continue
        
        return notifications
