from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import user as user_model
from app.utils.auth import get_current_user
from app.schemas.hierarchy import DepartmentHierarchy

router = APIRouter()


# 1. Get unique departments
@router.get("/departments", response_model=List[str])
def get_departments(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    departments = db.query(user_model.User.department).distinct().all()
    return [d[0] for d in departments]


# 2. Get unique roles
@router.get("/roles", response_model=List[str])
def get_roles(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    roles = db.query(user_model.User.role).distinct().all()
    return [r[0] for r in roles]


# 3. Get hierarchy (department → role → users)
@router.get("/structure", response_model=List[DepartmentHierarchy])
def get_hierarchy(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    users = db.query(user_model.User).all()
    hierarchy = []

    dept_map = {}
    for user in users:
        if user.department not in dept_map:
            dept_map[user.department] = {}

        if user.role not in dept_map[user.department]:
            dept_map[user.department][user.role] = []

        dept_map[user.department][user.role].append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
        })

    for dept, roles in dept_map.items():
        hierarchy.append({
            "department": dept,
            "roles": roles
        })

    return hierarchy
