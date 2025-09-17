# app/utils/notifications.py
"""
Utility functions for creating and managing notifications
"""

from sqlalchemy.orm import Session
from app.models import Notification, NotificationType, NotificationPriority
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.SYSTEM,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    Create a new notification for a user
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        priority: Priority level
        related_entity_type: Type of related entity (e.g., 'task', 'project')
        related_entity_id: ID of related entity
        expires_at: When the notification expires
        extra_data: Additional data as dict
    
    Returns:
        Created notification object
    """
    
    # Serialize extra_data if provided
    extra_data_json = json.dumps(extra_data) if extra_data else None
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        expires_at=expires_at,
        extra_data=extra_data_json
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification

def create_task_notification(
    db: Session,
    user_id: int,
    task_title: str,
    notification_type: NotificationType,
    task_id: Optional[int] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    additional_info: Optional[str] = None
) -> Notification:
    """
    Create a task-related notification
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        task_title: Title of the task
        notification_type: Type of task notification
        task_id: ID of the task
        priority: Priority level
        additional_info: Additional information to include
    
    Returns:
        Created notification object
    """
    
    # Define notification content based on type
    notification_content = {
        NotificationType.TASK_ASSIGNED: {
            "title": "New Task Assigned",
            "message": f"You have been assigned a new task: {task_title}"
        },
        NotificationType.TASK_UPDATED: {
            "title": "Task Updated",
            "message": f"Task '{task_title}' has been updated"
        },
        NotificationType.TASK_STATUS_CHANGED: {
            "title": "Task Status Changed",
            "message": f"Task '{task_title}' status has been changed"
        },
        NotificationType.TASK_DUE_SOON: {
            "title": "Task Due Soon",
            "message": f"Task '{task_title}' is due soon"
        },
        NotificationType.TASK_OVERDUE: {
            "title": "Task Overdue",
            "message": f"Task '{task_title}' is overdue"
        }
    }
    
    content = notification_content.get(notification_type, {
        "title": "Task Notification",
        "message": f"Update for task: {task_title}"
    })
    
    if additional_info:
        content["message"] += f" - {additional_info}"
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=content["title"],
        message=content["message"],
        notification_type=notification_type,
        priority=priority,
        related_entity_type="task",
        related_entity_id=task_id
    )

def create_team_notification(
    db: Session,
    user_id: int,
    team_name: str,
    notification_type: NotificationType,
    team_id: Optional[int] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    additional_info: Optional[str] = None
) -> Notification:
    """
    Create a team-related notification
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        team_name: Name of the team
        notification_type: Type of team notification
        team_id: ID of the team
        priority: Priority level
        additional_info: Additional information to include
    
    Returns:
        Created notification object
    """
    
    # Define notification content based on type
    notification_content = {
        NotificationType.TEAM_MEMBER_ADDED: {
            "title": "Added to Team",
            "message": f"You have been added to team '{team_name}'"
        },
        NotificationType.TEAM_MEMBER_REMOVED: {
            "title": "Removed from Team",
            "message": f"You have been removed from team '{team_name}'"
        }
    }
    
    content = notification_content.get(notification_type, {
        "title": "Team Notification",
        "message": f"Update for team: {team_name}"
    })
    
    if additional_info:
        content["message"] += f" - {additional_info}"
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=content["title"],
        message=content["message"],
        notification_type=notification_type,
        priority=priority,
        related_entity_type="team",
        related_entity_id=team_id
    )

def create_project_notification(
    db: Session,
    user_id: int,
    project_name: str,
    notification_type: NotificationType,
    project_id: Optional[int] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    additional_info: Optional[str] = None
) -> Notification:
    """
    Create a project-related notification
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        project_name: Name of the project
        notification_type: Type of project notification
        project_id: ID of the project
        priority: Priority level
        additional_info: Additional information to include
    
    Returns:
        Created notification object
    """
    
    # Define notification content based on type
    notification_content = {
        NotificationType.PROJECT_CREATED: {
            "title": "New Project Created",
            "message": f"New project '{project_name}' has been created"
        },
        NotificationType.PROJECT_UPDATED: {
            "title": "Project Updated",
            "message": f"Project '{project_name}' has been updated"
        }
    }
    
    content = notification_content.get(notification_type, {
        "title": "Project Notification",
        "message": f"Update for project: {project_name}"
    })
    
    if additional_info:
        content["message"] += f" - {additional_info}"
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=content["title"],
        message=content["message"],
        notification_type=notification_type,
        priority=priority,
        related_entity_type="project",
        related_entity_id=project_id
    )

def create_reminder_notification(
    db: Session,
    user_id: int,
    reminder_title: str,
    reminder_message: str,
    reminder_id: Optional[int] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Notification:
    """
    Create a reminder notification
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        reminder_title: Title of the reminder
        reminder_message: Message of the reminder
        reminder_id: ID of the reminder
        priority: Priority level
    
    Returns:
        Created notification object
    """
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=f"Reminder: {reminder_title}",
        message=reminder_message,
        notification_type=NotificationType.REMINDER,
        priority=priority,
        related_entity_type="reminder",
        related_entity_id=reminder_id
    )

def create_system_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    expires_at: Optional[datetime] = None
) -> Notification:
    """
    Create a system notification
    
    Args:
        db: Database session
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        priority: Priority level
        expires_at: When the notification expires
    
    Returns:
        Created notification object
    """
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationType.SYSTEM,
        priority=priority,
        expires_at=expires_at
    )

def cleanup_expired_notifications(db: Session) -> int:
    """
    Clean up expired notifications
    
    Args:
        db: Database session
    
    Returns:
        Number of notifications deleted
    """
    
    expired_notifications = db.query(Notification).filter(
        Notification.expires_at.isnot(None),
        Notification.expires_at < datetime.utcnow()
    ).all()
    
    count = len(expired_notifications)
    
    for notification in expired_notifications:
        db.delete(notification)
    
    db.commit()
    
    return count
