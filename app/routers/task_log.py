from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import task_log as log_model
from app.models import tasks as task_model
from app.schemas import task_log as log_schema
from app.database import get_db

router = APIRouter()

@router.get("/task/{task_id}", response_model=List[log_schema.LogResponse])
def get_logs_for_task(task_id: int, db: Session = Depends(get_db)):
    logs = db.query(log_model.TaskLog).filter(log_model.TaskLog.task_id == task_id).order_by(log_model.TaskLog.startTime.desc()).all()
    return logs

@router.post("/task/{task_id}", response_model=log_schema.LogResponse)
def create_log_for_task(task_id: int, log_data: log_schema.LogCreate, db: Session = Depends(get_db)):
    task = db.query(task_model.Task).filter(task_model.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    log = log_model.TaskLog(
        task_id=task_id,
        title=log_data.title,
        description=log_data.description,
        startTime=log_data.startTime,
        endTime=log_data.endTime,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
