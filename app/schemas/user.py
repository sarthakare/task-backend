from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    department: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# schemas/user.py
class UserBasic(BaseModel):
    id: int
    name: str
    department: str
    role: str

    model_config = {
        "from_attributes": True
    }


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str

    class Config:
        from_attributes = True