from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .user import UserBasic
from .team import TeamOut

class ProjectCreate(BaseModel):
    name: str
    description: str
    manager_id: int
    assigned_teams: List[int]
    start_date: datetime
    end_date: datetime
    status: Optional[str] = "active"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    assigned_teams: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class ProjectBase(BaseModel):
    id: int
    name: str
    description: str
    manager_id: int
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    manager_id: int
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    manager: UserBasic
    assigned_teams: List[TeamOut]

    model_config = {
        "from_attributes": True
    }

class ProjectTeamAdd(BaseModel):
    team_id: int

class ProjectTeamRemove(BaseModel):
    team_id: int
