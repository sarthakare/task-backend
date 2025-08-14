from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tasks as task_model
from app.schemas import tasks as task_schema
from app.models import user as user_model
from app.utils.auth import get_current_user
from datetime import date
from fastapi import Path
from sqlalchemy.exc import NoResultFound

router = APIRouter()

@router.post("/create", response_model=task_schema.TaskOut)
def create_task(
    task: task_schema.TaskCreate,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        print("📥 Received task payload:", task.dict())

        db_task = task_model.Task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            start_date=task.start_date,
            due_date=task.due_date,
            follow_up_date=task.follow_up_date,
            tags=task.tags,
            assigned_to=task.assigned_to,
            created_by=current_user.id,
        )

        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        print("✅ Task created with ID:", db_task.id)
        return db_task

    except Exception as e:
        print("❌ Error in create_task:", str(e))
        raise HTTPException(status_code=400, detail="Task creation failed")

@router.get("/all", response_model=task_schema.TaskListWithStats)
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        if current_user.role in ["admin", "manager"]:
            tasks = db.query(task_model.Task).all()
        else:
            tasks = db.query(task_model.Task).filter(
                (task_model.Task.created_by == current_user.id) |
                (task_model.Task.assigned_to == current_user.id)
            ).all()

        pydantic_tasks = [task_schema.TaskOut.model_validate(task) for task in tasks]

        today = date.today()
        stats = {
            "total": len(pydantic_tasks),
            "finished": sum(task.status == "FINISHED" for task in pydantic_tasks),
            "overdue": sum(task.due_date < today and task.status != "FINISHED" for task in pydantic_tasks),
            "upcoming": sum(task.due_date > today and task.status != "FINISHED" for task in pydantic_tasks),
        }

        return {
            **stats,
            "tasks": pydantic_tasks
        }

    except Exception as e:
        print("❌ Error in get_all_tasks:", str(e))
        raise HTTPException(status_code=500, detail="Could not fetch tasks")
    

@router.patch("/{task_id}/status", response_model=task_schema.TaskOut)
def update_task_status(
    task_id: int,
    status_update: task_schema.TaskStatusUpdate,  # no Depends()
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        # Fetch the task
        task = db.query(task_model.Task).filter(task_model.Task.id == task_id).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Update the status
        task.status = status_update.status
        db.commit()
        db.refresh(task)

        print(f"✅ Task {task.id} status updated to {task.status}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error in update_task_status:", str(e))
        raise HTTPException(status_code=500, detail="Could not update task status")
