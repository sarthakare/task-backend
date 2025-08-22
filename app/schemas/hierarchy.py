from pydantic import BaseModel
from typing import List, Dict

class HierarchyUser(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True   # ✅ allows reading from SQLAlchemy objects


class DepartmentHierarchy(BaseModel):
    department: str
    roles: Dict[str, List[HierarchyUser]]
