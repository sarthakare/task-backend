from pydantic import BaseModel
from typing import Literal

class ReportOut(BaseModel):
    userId: str
    userName: str
    completedTasks: int
    totalTasks: int
    overdueTasks: int
    escalatedTasks: int
    completionRate: float
    avgResponseTime: float
    department: str
    role: str
