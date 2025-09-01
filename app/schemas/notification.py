from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    task_id: Optional[int] = None
    type: Literal["ASSIGNMENT", "STATUS_CHANGE", "REMINDER", "ESCALATION"]
    title: str
    message: str

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class NotificationOut(BaseModel):
    id: int
    user_id: int
    task_id: Optional[int]
    type: Literal["ASSIGNMENT", "STATUS_CHANGE", "REMINDER", "ESCALATION"]
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class NotificationList(BaseModel):
    notifications: list[NotificationOut]
    total: int
    unread_count: int
