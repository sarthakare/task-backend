# app/routers/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import user as user_model
from app.schemas.user import UserBasic

router = APIRouter()

@router.get("/all", response_model=list[UserBasic])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(user_model.User).all()
