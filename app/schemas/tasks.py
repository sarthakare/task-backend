from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date, datetime
from app.schemas.user import UserOut
from app.schemas.task_log import LogResponse

class TaskCreate(BaseModel):
    # no change—clients still only send these
    title: str
    description: Optional[str]
    priority: Literal["LOW","MEDIUM","HIGH","CRITICAL"]
    start_date: datetime
    due_date: datetime
    follow_up_date: Optional[datetime]
    tags: List[str] = []
    assigned_to: int
    
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["LOW","MEDIUM","HIGH","CRITICAL"]] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: Literal["LOW","MEDIUM","HIGH","CRITICAL"]
    start_date: datetime
    due_date: datetime
    follow_up_date: Optional[datetime]
    tags: List[str]
    status: str

    # Who created it…
    created_by: int
    creator: UserOut            # ← nested user object
    created_at: datetime

    # …and who it’s assigned to
    assigned_to: int
    assignee: UserOut           # ← nested user object

    updated_at: Optional[datetime]
    
    # logs included in the response
    logs: List[LogResponse] = []

    model_config = {
        "from_attributes": True
    }

class TaskListWithStats(BaseModel):
    total: int
    finished: int
    overdue: int
    upcoming: int
    tasks: List[TaskOut]
    
class TaskStatusUpdate(BaseModel):
    status: str