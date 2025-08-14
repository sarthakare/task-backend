# app/schemas/tokens.py
from pydantic import BaseModel
from app.schemas.user import UserOut

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    
    class Config:
        from_attributes = True  # required for SQLAlchemy models in Pydantic v2