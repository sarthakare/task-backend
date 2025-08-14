from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogCreate(BaseModel):
    title: str
    description: Optional[str] = None
    startTime: datetime
    endTime: Optional[datetime] = None

class LogResponse(BaseModel):
    id: int
    task_id: int
    title: str
    description: Optional[str]
    startTime: datetime
    endTime: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
