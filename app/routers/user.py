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
    """Get users based on hierarchy - Admin sees all, others see from CEO down"""
    hierarchy_manager = HierarchyManager(db)
    
    if current_user.role == "ADMIN":
        # Admin can see all users including other admins (both active and inactive)
        return db.query(user_model.User).all()
    else:
        # Non-admin users see hierarchy from their level and below
        # First, try to get CEO as the top of non-admin hierarchy
        ceo_user = db.query(user_model.User).filter(
            user_model.User.role == "CEO",
            user_model.User.is_active == True
        ).first()
        
        if ceo_user:
            # If CEO exists, show CEO and all subordinates (both active and inactive)
            ceo_subordinates = hierarchy_manager.get_all_subordinates(ceo_user.id)
            subordinate_ids = [sub.id for sub in ceo_subordinates]
            subordinate_ids.append(ceo_user.id)  # Include CEO
            
            return db.query(user_model.User).filter(
                user_model.User.id.in_(subordinate_ids)
            ).all()
        else:
            # If no CEO exists, show all non-admin users (both active and inactive)
            return db.query(user_model.User).filter(
                user_model.User.role != "ADMIN"
            ).all()

@router.get("/active", response_model=List[UserBasic])
def get_active_users(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get active users based on hierarchy - Admin sees all, others see from CEO down"""
    hierarchy_manager = HierarchyManager(db)
    
    if current_user.role == "ADMIN":
        # Admin can see all active users including other admins
        return db.query(user_model.User).filter(user_model.User.is_active == True).all()
    else:
        # Non-admin users see hierarchy from their level and below
        ceo_user = db.query(user_model.User).filter(
            user_model.User.role == "CEO",
            user_model.User.is_active == True
        ).first()
        
        if ceo_user:
            # If CEO exists, show CEO and all subordinates
            ceo_subordinates = hierarchy_manager.get_all_subordinates(ceo_user.id)
            subordinate_ids = [sub.id for sub in ceo_subordinates]
            subordinate_ids.append(ceo_user.id)  # Include CEO
            
            return db.query(user_model.User).filter(
                user_model.User.id.in_(subordinate_ids),
                user_model.User.is_active == True
            ).all()
        else:
            # If no CEO exists, show all active non-admin users
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
    """Create a new user"""
    # Check if email already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Role hierarchy validation
    role_hierarchy = {
        "ADMIN": ["CEO", "manager", "team_lead", "member", "intern"],
        "CEO": ["manager", "team_lead", "member", "intern"],
        "manager": ["team_lead", "member", "intern"],
        "team_lead": ["member", "intern"],
        "member": ["intern"],
        "intern": []
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
def get_supervisors(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """Get users for supervisor selection based on hierarchy"""
    hierarchy_manager = HierarchyManager(db)
    
    if current_user.role == "ADMIN":
        # Admin can see all users as potential supervisors
        return db.query(user_model.User).filter(
            user_model.User.is_active == True
        ).all()
    else:
        # Non-admin users see hierarchy from their level and below for supervisor selection
        ceo_user = db.query(user_model.User).filter(
            user_model.User.role == "CEO",
            user_model.User.is_active == True
        ).first()
        
        if ceo_user:
            # If CEO exists, show CEO and all subordinates
            ceo_subordinates = hierarchy_manager.get_all_subordinates(ceo_user.id)
            subordinate_ids = [sub.id for sub in ceo_subordinates]
            subordinate_ids.append(ceo_user.id)  # Include CEO
            
            return db.query(user_model.User).filter(
                user_model.User.id.in_(subordinate_ids),
                user_model.User.is_active == True
            ).all()
        else:
            # If no CEO exists, show all non-admin users for supervisor selection
            return db.query(user_model.User).filter(
                user_model.User.role != "ADMIN",
                user_model.User.is_active == True
            ).all()

@router.get("/departments/")
def get_departments(current_user: user_model.User = Depends(get_current_user)):
    """Get list of available departments"""
    base_departments = [
        "engineering",
        "marketing", 
        "sales",
        "hr",
        "finance",
        "operations",
        "it"
    ]
    
    # Only admin can create CEO users with "All" department
    if current_user.role.upper() == "ADMIN":
        return ["All"] + base_departments
    
    return base_departments

@router.get("/roles/")
def get_roles(current_user: user_model.User = Depends(get_current_user)):
    """Get list of available roles based on hierarchy"""
    # Define role hierarchy: admin -> ceo -> manager -> team_lead -> member -> intern
    role_hierarchy = {
        "ADMIN": ["CEO", "manager", "team_lead", "member", "intern"],
        "CEO": ["manager", "team_lead", "member", "intern"],
        "manager": ["team_lead", "member", "intern"],
        "team_lead": ["member", "intern"],
        "member": ["intern"],
        "intern": []
    }
    
    # Get available roles for current user
    available_roles = role_hierarchy.get(current_user.role.upper(), [])
    return available_roles

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
    roles = ['CEO', 'manager', 'team_lead', 'member', 'intern']
    for role in roles:
        count = db.query(user_model.User).filter(
            user_model.User.role == role,
            user_model.User.is_active == True
        ).count()
        role_counts[role] = count
    
    # Count by department (excluding admin users)
    department_counts = {}
    departments = ['All', 'engineering', 'marketing', 'sales', 'hr', 'finance', 'operations', 'it']
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
