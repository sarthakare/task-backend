from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
from app.database import get_db
from app.models import tasks as task_model, user as user_model
from app.utils.auth import get_current_user
from typing import List
from app.schemas.reports import ReportOut

router = APIRouter()

@router.get("/all", response_model=List[ReportOut])
def get_reports(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        # 🔹 Fetch all users (you may want to filter only active ones)
        users = db.query(user_model.User).all()
        today = datetime.utcnow()

        reports = []
        for user in users:
            tasks = db.query(task_model.Task).filter(
                task_model.Task.assigned_to == user.id
            ).all()

            total_tasks = len(tasks)
            completed_tasks = sum(task.status == "FINISHED" for task in tasks)
            overdue_tasks = sum(
                task.due_date and task.due_date < today and task.status != "FINISHED"
                for task in tasks
            )
            escalated_tasks = sum(
                getattr(task, "is_escalated", False) for task in tasks
            )

            # Completion rate %
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Avg Response Time (dummy: due_date - start_date) → you can refine logic
            response_times = [
                (task.due_date - task.start_date).days
                for task in tasks
                if task.start_date and task.due_date
            ]
            avg_response_time = round(sum(response_times) / len(response_times), 2) if response_times else 0

            reports.append({
                "userId": str(user.id),
                "userName": user.name,
                "completedTasks": completed_tasks,
                "totalTasks": total_tasks,
                "overdueTasks": overdue_tasks,
                "escalatedTasks": escalated_tasks,
                "completionRate": completion_rate,
                "avgResponseTime": avg_response_time,
            })

        return reports

    except Exception as e:
        print("❌ Error in get_reports:", str(e))
        raise HTTPException(status_code=500, detail="Could not fetch reports")
