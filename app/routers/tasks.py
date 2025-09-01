from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tasks as task_model
from app.schemas import tasks as task_schema
from app.models import user as user_model
from app.utils.auth import get_current_user
from datetime import datetime
from fastapi import Path
from sqlalchemy.exc import NoResultFound
from app.services.notification_service import NotificationService

router = APIRouter()

@router.post("/create", response_model=task_schema.TaskOut)
async def create_task(
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
        
        # Send notification to assigned user if different from creator
        if task.assigned_to != current_user.id:
            try:
                # Get the assigned user
                assigned_user = db.query(user_model.User).filter(
                    user_model.User.id == task.assigned_to
                ).first()
                
                if assigned_user:
                    # Create and send notification
                    await NotificationService.create_task_assignment_notification(
                        db=db,
                        task=db_task,
                        assigned_user=assigned_user,
                        creator_user=current_user
                    )
                    print(f"✅ Notification sent to user {assigned_user.name} for task assignment")
                else:
                    print(f"⚠️ Assigned user {task.assigned_to} not found")
                    
            except Exception as notification_error:
                print(f"⚠️ Error sending notification: {notification_error}")
                # Don't fail the task creation if notification fails
        
        return db_task

    except Exception as e:
        print("❌ Error in create_task:", str(e))
        raise HTTPException(status_code=400, detail="Task creation failed")
    
    
@router.put("/{task_id}", response_model=task_schema.TaskOut)
def update_task(
    task_id: int,
    task_update: task_schema.TaskUpdate,  # This schema should allow partial updates
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        print(f"📥 Updating task {task_id} with data:", task_update.dict())
        # Fetch the task
        task = db.query(task_model.Task).filter(
            task_model.Task.id == task_id,
            task_model.Task.assigned_to == current_user.id  # ensure only assignee can update
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found or not assigned to you")

        # Apply updates (only fields provided in request)
        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        db.commit()
        db.refresh(task)

        print(f"✅ Task {task.id} updated with data: {update_data}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error in update_task:", str(e))
        raise HTTPException(status_code=500, detail="Could not update task")


@router.get("/all", response_model=task_schema.TaskListWithStats)
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    try:
        # ✅ Only tasks assigned to current user
        tasks = db.query(task_model.Task).filter(
            task_model.Task.assigned_to == current_user.id
        ).all()

        pydantic_tasks = [task_schema.TaskOut.model_validate(task) for task in tasks]

        today = datetime.today()
        stats = {
            "total": len(pydantic_tasks),
            "finished": sum(task.status == "FINISHED" for task in pydantic_tasks),
            "overdue": sum(
                task.due_date < today and task.status != "FINISHED"
                for task in pydantic_tasks
            ),
            "upcoming": sum(
                task.due_date > today and task.status != "FINISHED"
                for task in pydantic_tasks
            ),
        }

        return {**stats, "tasks": pydantic_tasks}

    except Exception as e:
        print("❌ Error in get_all_tasks:", str(e))
        raise HTTPException(status_code=500, detail="Could not fetch tasks")


@router.patch("/{task_id}/status", response_model=task_schema.TaskOut)
async def update_task_status(
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

        # Store old status for notification
        old_status = task.status

        # Update the status
        task.status = status_update.status
        db.commit()
        db.refresh(task)

        print(f"✅ Task {task.id} status updated to {task.status}")
        
        # Send notification to task creator about status change
        if task.created_by != current_user.id:
            try:
                # Get the task creator
                creator_user = db.query(user_model.User).filter(
                    user_model.User.id == task.created_by
                ).first()
                
                if creator_user:
                    # Create and send notification
                    await NotificationService.create_task_status_change_notification(
                        db=db,
                        task=task,
                        old_status=old_status,
                        new_status=task.status,
                        updated_by=current_user
                    )
                    print(f"✅ Status change notification sent to task creator {creator_user.name}")
                else:
                    print(f"⚠️ Task creator {task.created_by} not found")
                    
            except Exception as notification_error:
                print(f"⚠️ Error sending status change notification: {notification_error}")
                # Don't fail the status update if notification fails
        
        return task

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error in update_task_status:", str(e))
        raise HTTPException(status_code=500, detail="Could not update task status")
