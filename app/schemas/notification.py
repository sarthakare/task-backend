# app/schemas/notification.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationType, NotificationPriority

class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

class NotificationOut(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    is_archived: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NotificationSummary(BaseModel):
    id: int
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    is_read: bool
    created_at: datetime
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    archived_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]

class BulkNotificationUpdate(BaseModel):
    notification_ids: list[int]
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None

class NotificationMarkAllRead(BaseModel):
    user_id: int
    notification_type: Optional[NotificationType] = None
