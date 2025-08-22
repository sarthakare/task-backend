from pydantic import BaseModel

class ReportOut(BaseModel):
    userId: str
    userName: str
    completedTasks: int
    totalTasks: int
    overdueTasks: int
    escalatedTasks: int
    completionRate: float
    avgResponseTime: float
