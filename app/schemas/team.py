from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .user import UserBasic

class TeamCreate(BaseModel):
    name: str
    description: str
    department: str
    leader_id: int
    member_ids: List[int]
    status: Optional[str] = "active"

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    leader_id: Optional[int] = None
    member_ids: Optional[List[int]] = None
    status: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class TeamBase(BaseModel):
    id: int
    name: str
    description: str
    department: str
    leader_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    department: str
    leader_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    leader: UserBasic
    members: List[UserBasic]

    model_config = {
        "from_attributes": True
    }

class TeamMemberAdd(BaseModel):
    user_id: int

class TeamMemberRemove(BaseModel):
    user_id: int
