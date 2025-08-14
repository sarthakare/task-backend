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
    start_date: date
    due_date: date
    follow_up_date: Optional[date]
    tags: List[str] = []
    assigned_to: int

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: Literal["LOW","MEDIUM","HIGH","CRITICAL"]
    start_date: date
    due_date: date
    follow_up_date: Optional[date]
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