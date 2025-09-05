# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import user as user_model
from app.schemas.user import UserBasic, UserCreate, UserOut, UserUpdate, SupervisorList
from app.utils.security import get_password_hash
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserBasic])
def get_all_users(db: Session = Depends(get_db)):
    """Get all users"""
    return db.query(user_model.User).all()

@router.get("/active", response_model=List[UserBasic])
def get_active_users(db: Session = Depends(get_db)):
    """Get all active users"""
    return db.query(user_model.User).filter(user_model.User.is_active == True).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if supervisor exists if provided
    if user.supervisor_id:
        supervisor = db.query(user_model.User).filter(user_model.User.id == user.supervisor_id).first()
        if not supervisor:
            raise HTTPException(status_code=400, detail="Supervisor not found")
        if not supervisor.is_active:
            raise HTTPException(status_code=400, detail="Supervisor is not active")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = user_model.User(
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        hashed_password=hashed_password,
        department=user.department,
        role=user.role,
        supervisor_id=user.supervisor_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user"""
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email already exists for another user
    if user_update.email and user_update.email != db_user.email:
        existing_user = db.query(user_model.User).filter(
            user_model.User.email == user_update.email,
            user_model.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if supervisor exists if provided
    if user_update.supervisor_id and user_update.supervisor_id != db_user.supervisor_id:
        if user_update.supervisor_id == user_id:
            raise HTTPException(status_code=400, detail="User cannot be their own supervisor")
        supervisor = db.query(user_model.User).filter(user_model.User.id == user_update.supervisor_id).first()
        if not supervisor:
            raise HTTPException(status_code=400, detail="Supervisor not found")
        if not supervisor.is_active:
            raise HTTPException(status_code=400, detail="Supervisor is not active")
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (soft delete by setting is_active to False)"""
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete
    db_user.is_active = False
    db.commit()
    return None

@router.get("/supervisors/", response_model=List[SupervisorList])
def get_supervisors(db: Session = Depends(get_db)):
    """Get all users for supervisor selection (all active users with their details)"""
    return db.query(user_model.User).filter(
        user_model.User.is_active == True
    ).all()

@router.get("/departments/")
def get_departments():
    """Get list of available departments"""
    return [
        "engineering",
        "marketing", 
        "sales",
        "hr",
        "finance",
        "operations",
        "it"
    ]

@router.get("/roles/")
def get_roles():
    """Get list of available roles"""
    return [
        "manager",
        "team_lead",
        "member",
        "intern"
    ]

@router.get("/stats/")
def get_user_stats(db: Session = Depends(get_db)):
    """Get user statistics"""
    total_users = db.query(user_model.User).count()
    active_users = db.query(user_model.User).filter(user_model.User.is_active == True).count()
    
    # Count by role
    role_counts = {}
    roles = ['admin', 'manager', 'supervisor', 'team_lead', 'member', 'intern']
    for role in roles:
        count = db.query(user_model.User).filter(
            user_model.User.role == role,
            user_model.User.is_active == True
        ).count()
        role_counts[role] = count
    
    # Count by department
    department_counts = {}
    departments = ['engineering', 'marketing', 'sales', 'hr', 'finance', 'operations', 'it']
    for dept in departments:
        count = db.query(user_model.User).filter(
            user_model.User.department == dept,
            user_model.User.is_active == True
        ).count()
        department_counts[dept] = count
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "role_counts": role_counts,
        "department_counts": department_counts
    }
