from pydantic import BaseModel
from typing import List, Dict

class HierarchyUser(BaseModel):
    id: int
    name: str
    email: str

    model_config = {
        "from_attributes": True
    }

class DepartmentHierarchy(BaseModel):
    department: str
    roles: Dict[str, List[HierarchyUser]]
