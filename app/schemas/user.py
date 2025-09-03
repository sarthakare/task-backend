from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: Optional[str] = None
    password: str
    department: str
    role: str
    supervisor_id: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SupervisorList(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str

    model_config = {
        "from_attributes": True
    }

class UserBasic(BaseModel):
    id: int
    name: str
    email: str
    mobile: Optional[str] = None
    department: str
    role: str
    supervisor_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: Optional[str] = None
    department: str
    role: str
    supervisor_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    supervisor_id: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = {
        "from_attributes": True
    }