# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.models import user as user_model
from app.schemas.user import UserBasic, UserCreate, UserOut, UserUpdate, SupervisorList
from app.utils.security import get_password_hash
from app.utils.auth import get_current_user
from app.utils.hierarchy import HierarchyManager

router = APIRouter()

@router.get("/", response_model=List[UserBasic])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get all users - Same list for everyone (excluding admin users from non-admin users)"""
    
    # Show all users except admin users to non-admin users
    if current_user.role == "ADMIN":
        # Admin can see all users including other admins (both active and inactive)
        return db.query(user_model.User).all()
    else:
        # Non-admin users see all users except admin users (both active and inactive)
        return db.query(user_model.User).filter(
            user_model.User.role != "ADMIN"
        ).all()

@router.get("/active", response_model=List[UserBasic])
def get_active_users(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get active users - Same list for everyone (excluding admin users from non-admin users)"""
    
    # Show all active users except admin users to non-admin users
    if current_user.role == "ADMIN":
        # Admin can see all active users including other admins
        return db.query(user_model.User).filter(user_model.User.is_active == True).all()
    else:
        # Non-admin users see all active users except admin users
        return db.query(user_model.User).filter(
            user_model.User.role != "ADMIN",
            user_model.User.is_active == True
        ).all()

@router.get("/me")
def get_current_user_info(current_user: user_model.User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: user_model.User = Depends(get_current_user)):
    """Create a new user - Only ADMIN and CEO can create users"""
    # Authorization check: Only ADMIN and CEO can create users
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only ADMIN and CEO can create users"
        )
    
    # Check if email already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Role hierarchy validation
    role_hierarchy = {
        "ADMIN": ["CEO", "manager", "team_lead", "member"],
        "CEO": ["manager", "team_lead", "member"],
        "manager": ["team_lead", "member"],
        "team_lead": ["member"],
        "member": []
    }
    
    allowed_roles = role_hierarchy.get(current_user.role.upper(), [])
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"You don't have permission to create users with role '{user.role}'")
    
    # CEO role specific validations
    if user.role.upper() == "CEO":
        if current_user.role.upper() != "ADMIN":
            raise HTTPException(status_code=403, detail="Only admin can create CEO users")
        
        # Check if CEO already exists
        existing_ceo = db.query(user_model.User).filter(
            user_model.User.role.ilike("CEO"),
            user_model.User.is_active == True
        ).first()
        if existing_ceo:
            raise HTTPException(status_code=400, detail="CEO user already exists. Only one CEO is allowed.")
        
        # CEO must have "All" department
        if user.department != "All":
            user.department = "All"
    
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
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: user_model.User = Depends(get_current_user)):
    """Update a user - Only ADMIN and CEO can update user status"""
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Authorization check for sensitive fields: Only ADMIN and CEO can modify user status and role
    if user_update.is_active is not None or user_update.role is not None:
        if current_user.role.upper() not in ["ADMIN", "CEO"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Only ADMIN and CEO can modify user status and role"
            )
    
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
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update separately (hash it if provided)
    if 'password' in update_data:
        password = update_data.pop('password')
        if password:  # Only hash if password is not empty
            hashed_password = get_password_hash(password)
            setattr(db_user, 'hashed_password', hashed_password)
    
    # Update other fields
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: user_model.User = Depends(get_current_user)):
    """Delete a user (soft delete by setting is_active to False) - Only ADMIN and CEO can delete users"""
    # Authorization check: Only ADMIN and CEO can delete users
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only ADMIN and CEO can delete users"
        )
    
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent users from deleting themselves
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot delete your own account"
        )
    
    # Soft delete
    db_user.is_active = False
    db.commit()
    return None

@router.get("/supervisors/", response_model=List[SupervisorList])
def get_supervisors(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get users for supervisor selection - Same list for everyone (excluding admin users from non-admin users)"""
    
    # Show all active users except admin users to non-admin users for supervisor selection
    if current_user.role == "ADMIN":
        # Admin can see all users as potential supervisors
        return db.query(user_model.User).filter(
            user_model.User.is_active == True
        ).all()
    else:
        # Non-admin users see all active users except admin users for supervisor selection
        return db.query(user_model.User).filter(
            user_model.User.role != "ADMIN",
            user_model.User.is_active == True
        ).all()

@router.get("/departments/")
def get_departments(current_user: user_model.User = Depends(get_current_user)):
    """Get list of available departments"""
    base_departments = [
        "Engineering",
        "Marketing", 
        "Sales",
        "HR",
        "Finance",
        "Operations",
        "IT"
    ]
    
    # Only admin can create CEO users with "All" department
    if current_user.role.upper() == "ADMIN":
        return ["All"] + base_departments
    
    return base_departments

@router.get("/roles/")
def get_roles(current_user: user_model.User = Depends(get_current_user)):
    """Get list of available roles"""
    # Return all available roles for any user
    return ["CEO", "manager", "team_lead", "member"]

@router.get("/stats/")
def get_user_stats(db: Session = Depends(get_db)):
    """Get user statistics (excluding admin users)"""
    # Count total users excluding admin
    total_users = db.query(user_model.User).filter(
        user_model.User.role != "ADMIN"
    ).count()
    
    # Count active users excluding admin
    active_users = db.query(user_model.User).filter(
        user_model.User.is_active == True,
        user_model.User.role != "ADMIN"
    ).count()
    
    # Count by role (excluding admin)
    role_counts = {}
    roles = ['CEO', 'manager', 'team_lead', 'member']
    for role in roles:
        count = db.query(user_model.User).filter(
            user_model.User.role == role,
            user_model.User.is_active == True
        ).count()
        role_counts[role] = count
    
    # Count by department (excluding admin users)
    department_counts = {}
    departments = ['All', 'Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations', 'IT']
    for dept in departments:
        count = db.query(user_model.User).filter(
            user_model.User.department == dept,
            user_model.User.is_active == True,
            user_model.User.role != "ADMIN"
        ).count()
        department_counts[dept] = count
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "users_by_role": role_counts,
        "users_by_department": department_counts
    }
