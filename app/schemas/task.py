# app/schemas/task.py
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TaskStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"

class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TaskBase(BaseModel):
    title: str
    description: str
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_to: int
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: datetime
    due_date: datetime
    follow_up_date: datetime

    @validator('due_date')
    def due_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Due date must be after start date')
        return v

    @validator('follow_up_date')
    def follow_up_date_validation(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('Follow-up date cannot be before start date')
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_to: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None

# For returning task data
class UserBasic(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str

    class Config:
        from_attributes = True

class TeamBasic(BaseModel):
    id: int
    name: str
    department: str

    class Config:
        from_attributes = True

class ProjectBasic(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True

class TaskLogOut(BaseModel):
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Task Attachment Schemas
class TaskAttachmentOut(BaseModel):
    id: int
    task_id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskAttachmentCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str

class TaskAttachmentUpdate(BaseModel):
    filename: Optional[str] = None
    original_filename: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    created_by: int
    assigned_to: int
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    status: TaskStatus
    priority: TaskPriority
    start_date: datetime
    due_date: datetime
    follow_up_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Related objects
    creator: UserBasic
    assignee: UserBasic
    project: Optional[ProjectBasic] = None
    team: Optional[TeamBasic] = None
    logs: List[TaskLogOut] = []
    attachments: List[TaskAttachmentOut] = []

    class Config:
        from_attributes = True

class TaskLogCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None

class TaskLogUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

