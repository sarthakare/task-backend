# app/schemas/reminder.py
from pydantic import BaseModel, validator
from datetime import datetime, date
from typing import Optional

class ReminderBase(BaseModel):
    title: str
    description: str
    due_date: date  # Date only, no time component
    priority: str = "MEDIUM"
    user_id: int
    task_id: Optional[int] = None

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None  # Date only, no time component
    priority: Optional[str] = None
    user_id: Optional[int] = None
    task_id: Optional[int] = None
    is_completed: Optional[bool] = None

    @validator('priority')
    def validate_priority(cls, v):
        if v is not None:
            valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            if v not in valid_priorities:
                raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v

# For returning reminder data
class UserBasic(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class TaskBasic(BaseModel):
    id: int
    title: str
    status: str

    class Config:
        from_attributes = True

class ReminderOut(BaseModel):
    id: int
    title: str
    description: str
    due_date: date  # Date only, no time component
    priority: str
    created_by: int
    user_id: int
    task_id: Optional[int] = None
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Related objects
    creator: UserBasic
    user: UserBasic
    task: Optional[TaskBasic] = None

    class Config:
        from_attributes = True
