# app/routers/task.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime
import asyncio

from app.database import get_db
from app.models import Task, TaskLog, User, Project, Team, TaskStatus as TaskStatusEnum
from app.schemas import TaskCreate, TaskUpdate, TaskOut, TaskLogCreate, TaskLogOut
from app.utils.auth import get_current_user
from app.utils.hierarchy import HierarchyManager
from app.utils.notifications import create_task_notification

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Import WebSocket notification functions from main.py
# We'll need to import these functions to send notifications
async def send_task_notification(
    notification_type: str,
    title: str,
    message: str,
    target_user_id: Optional[int] = None,
    task_data: Optional[dict] = None
):
    """Send task-related WebSocket notification"""
    try:
        # Import here to avoid circular imports
        from main import send_toast, MessageTarget, send_to_user, broadcast_message, active_connections
        import json
        
        print(f"Sending task notification: {notification_type} to user {target_user_id}")
        print(f"Active connections: {list(active_connections.keys())}")
        
        notification_data = {
            "type": "task_notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "task_data": task_data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        json_message = json.dumps(notification_data)
        
        if target_user_id:
            print(f"Attempting to send to user {target_user_id}")
            await send_to_user(target_user_id, json_message)
        else:
            print("Broadcasting to all users")
            await broadcast_message(json_message)
            
    except Exception as e:
        print(f"Error sending task notification: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the main operation if notification fails

def serialize_enum(obj):
    """Helper function to serialize enum objects to their string values"""
    if hasattr(obj, 'value'):
        return obj.value
    return str(obj)

def send_notification_async(
    notification_type: str,
    title: str,
    message: str,
    target_user_id: Optional[int] = None,
    task_data: Optional[dict] = None
):
    """Helper function to send notifications asynchronously from sync context"""
    import threading
    
    def run_notification():
        try:
            # Ensure task_data is properly serialized
            if task_data:
                serialized_task_data = {}
                for key, value in task_data.items():
                    if hasattr(value, 'value'):  # Handle enums
                        serialized_task_data[key] = value.value
                    elif hasattr(value, 'isoformat'):  # Handle datetime
                        serialized_task_data[key] = value.isoformat()
                    else:
                        serialized_task_data[key] = value
            else:
                serialized_task_data = None
                
            asyncio.run(send_task_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                target_user_id=target_user_id,
                task_data=serialized_task_data
            ))
        except Exception as e:
            print(f"Error in notification thread: {e}")
            import traceback
            traceback.print_exc()
    
    # Run in a separate thread to avoid blocking the main request
    thread = threading.Thread(target=run_notification, daemon=True)
    thread.start()

@router.get("/", response_model=List[TaskOut])
def get_all_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    show_all: bool = False,  # Admin/supervisor override
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks with role-based access control
    
    Role-based task visibility:
    - ADMIN and CEO: see all tasks
    - MANAGER: see own + team_lead + member tasks
    - TEAM_LEAD: see own + member tasks  
    - MEMBER: see only own tasks
    """
    hierarchy_manager = HierarchyManager(db)
    
    query = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    )
    
    # Apply role-based filtering
    role = current_user.role.upper()
    
    if role in ['ADMIN', 'CEO']:
        # ADMIN and CEO can see all tasks - no filtering needed
        pass
    else:
        # Get user IDs that current user can view based on role
        viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
        
        # Filter tasks that user can view based on role scope
        query = query.filter(
            or_(
                Task.created_by.in_(viewable_user_ids),
                Task.assigned_to.in_(viewable_user_ids)
            )
        )
    
    # Apply additional filters
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if team_id:
        query = query.filter(Task.team_id == team_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # Additional security check for non-admin/ceo users
    if role not in ['ADMIN', 'CEO']:
        accessible_tasks = []
        for task in tasks:
            if hierarchy_manager.can_view_task_by_role(current_user.id, task.created_by, task.assigned_to):
                accessible_tasks.append(task)
        return accessible_tasks
    
    return tasks

@router.get("/access-scope", response_model=dict)
def get_access_scope(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get information about current user's task access scope based on role"""
    hierarchy_manager = HierarchyManager(db)
    return hierarchy_manager.get_access_scope_info(current_user.id)

@router.get("/{task_id}/can-edit", response_model=dict)
def can_edit_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if current user can edit a specific task"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can modify this task
    can_edit = hierarchy_manager.can_modify_task(current_user.id, task.created_by, task.assigned_to)
    
    return {
        "can_edit": can_edit,
        "user_id": current_user.id,
        "user_role": current_user.role,
        "task_id": task_id
    }

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task by ID with role-based access control"""
    hierarchy_manager = HierarchyManager(db)
    
    task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can view this task based on role-based scope
    if not hierarchy_manager.can_view_task_by_role(current_user.id, task.created_by, task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this task"
        )
    
    return task

@router.post("/", response_model=TaskOut)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task with hierarchy-based assignment validation"""
    hierarchy_manager = HierarchyManager(db)
    
    # Validate assignee exists and is active
    assignee = db.query(User).filter(User.id == task.assigned_to, User.is_active == True).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user not found or inactive"
        )
    
    # Validate assignment is allowed based on hierarchy
    if not hierarchy_manager.is_peer_or_subordinate(current_user.id, task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign tasks to your subordinates or peers. Cannot assign tasks to superiors."
        )
    
    # Validate project if provided
    if task.project_id:
        project = db.query(Project).filter(
            Project.id == task.project_id,
            Project.status.in_(["active"])
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or not active"
            )
    
    # Validate team if provided
    if task.team_id:
        team = db.query(Team).filter(
            Team.id == task.team_id,
            Team.status == "active"
        ).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found or not active"
            )
    
    # Create the task
    db_task = Task(
        title=task.title,
        description=task.description,
        created_by=current_user.id,
        assigned_to=task.assigned_to,
        project_id=task.project_id,
        team_id=task.team_id,
        status=task.status,
        priority=task.priority,
        start_date=task.start_date,
        due_date=task.due_date,
        follow_up_date=task.follow_up_date
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    # Create database notification for the assigned user
    try:
        from app.models.notification import NotificationType, NotificationPriority
        
        # Create notification in database
        create_task_notification(
            db=db,
            user_id=db_task.assigned_to,
            task_title=db_task.title,
            notification_type=NotificationType.TASK_ASSIGNED,
            task_id=db_task.id,
            priority=NotificationPriority.HIGH if db_task.priority == "CRITICAL" else 
                    NotificationPriority.MEDIUM if db_task.priority == "HIGH" else 
                    NotificationPriority.LOW,
            additional_info=f"Assigned by {db_task.creator.name}"
        )
        print(f"Database notification created for user {db_task.assigned_to}")
    except Exception as e:
        print(f"Error creating database notification: {e}")
        # Don't fail the main operation if notification fails

    # Send WebSocket notification to the assigned user
    try:
        # Create task data for notification
        task_data = {
            "task_id": db_task.id,
            "title": db_task.title,
            "description": db_task.description,
            "priority": db_task.priority,
            "status": db_task.status,
            "due_date": db_task.due_date,
            "project_name": db_task.project.name if db_task.project else None,
            "team_name": db_task.team.name if db_task.team else None,
            "creator_name": db_task.creator.name,
            "assignee_name": db_task.assignee.name
        }
        
        # Send notification to assigned user
        send_notification_async(
            notification_type="task_assigned",
            title="New Task Assigned",
            message=f"You have been assigned a new task: '{db_task.title}' by {db_task.creator.name}",
            target_user_id=db_task.assigned_to,
            task_data=task_data
        )
        
        # Also send a general notification to team/department if applicable
        if db_task.team:
            send_notification_async(
                notification_type="team_task_created",
                title="New Team Task",
                message=f"New task '{db_task.title}' has been created for team {db_task.team.name}",
                target_user_id=None,  # Broadcast to team
                task_data=task_data
            )
            
    except Exception as e:
        print(f"Error sending task assignment notification: {e}")
        # Don't fail the main operation if notification fails
    
    return db_task

@router.put("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update only the status of a task with more permissive access control"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can update status of this task
    if not hierarchy_manager.can_update_task_status(current_user.id, db_task.created_by, db_task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task's status"
        )
    
    # Validate status
    new_status = status_update.get('status')
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status value
    valid_statuses = [status.value for status in TaskStatusEnum]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update only the status
    db_task.status = new_status
    
    # Set completed_at if status is FINISHED
    if new_status == TaskStatusEnum.FINISHED and db_task.completed_at is None:
        db_task.completed_at = datetime.utcnow()
    elif new_status != TaskStatusEnum.FINISHED:
        db_task.completed_at = None
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    # Create database notifications for status update
    try:
        from app.models.notification import NotificationType, NotificationPriority
        
        # Notify the task creator about status change
        if db_task.created_by != current_user.id:
            create_task_notification(
                db=db,
                user_id=db_task.created_by,
                task_title=db_task.title,
                notification_type=NotificationType.TASK_STATUS_CHANGED,
                task_id=db_task.id,
                priority=NotificationPriority.MEDIUM,
                additional_info=f"Status changed to '{db_task.status}' by {current_user.name}"
            )
            print(f"Database status notification created for creator {db_task.created_by}")
        
        # Notify the assignee if they're not the one updating
        if db_task.assigned_to != current_user.id:
            create_task_notification(
                db=db,
                user_id=db_task.assigned_to,
                task_title=db_task.title,
                notification_type=NotificationType.TASK_STATUS_CHANGED,
                task_id=db_task.id,
                priority=NotificationPriority.MEDIUM,
                additional_info=f"Status changed to '{db_task.status}' by {current_user.name}"
            )
            print(f"Database status notification created for assignee {db_task.assigned_to}")
    except Exception as e:
        print(f"Error creating database status notification: {e}")
        # Don't fail the main operation if notification fails

    # Send WebSocket notification for status update
    try:
        task_data = {
            "task_id": db_task.id,
            "title": db_task.title,
            "status": db_task.status,
            "updated_by": current_user.name,
            "assignee_name": db_task.assignee.name,
            "creator_name": db_task.creator.name
        }
        
        # Notify the task creator about status change
        if db_task.created_by != current_user.id:
            send_notification_async(
                notification_type="task_status_updated",
                title="Task Status Updated",
                message=f"Task '{db_task.title}' status has been updated to '{db_task.status}' by {current_user.name}",
                target_user_id=db_task.created_by,
                task_data=task_data
            )
        
        # Notify the assignee if they're not the one updating
        if db_task.assigned_to != current_user.id:
            send_notification_async(
                notification_type="task_status_updated",
                title="Task Status Updated",
                message=f"Your task '{db_task.title}' status has been updated to '{db_task.status}' by {current_user.name}",
                target_user_id=db_task.assigned_to,
                task_data=task_data
            )
            
    except Exception as e:
        print(f"Error sending task status update notification: {e}")
    
    return db_task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a task with hierarchy-based access control"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get the task
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user can modify this task
    if not hierarchy_manager.can_modify_task(current_user.id, db_task.created_by, db_task.assigned_to):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this task"
        )
    
    # Validate assignee if being updated
    if task_update.assigned_to:
        assignee = db.query(User).filter(
            User.id == task_update.assigned_to,
            User.is_active == True
        ).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not found or inactive"
            )
        
        # Validate assignment is allowed based on hierarchy
        if not hierarchy_manager.is_peer_or_subordinate(current_user.id, task_update.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign tasks to your subordinates or peers. Cannot assign tasks to superiors."
            )
    
    # Validate project if being updated
    if task_update.project_id:
        project = db.query(Project).filter(
            Project.id == task_update.project_id,
            Project.status.in_(["active"])
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or not active"
            )
    
    # Validate team if being updated
    if task_update.team_id:
        team = db.query(Team).filter(
            Team.id == task_update.team_id,
            Team.status == "active"
        ).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found or not active"
            )
    
    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Set completed_at if status is FINISHED
    if task_update.status == TaskStatusEnum.FINISHED and db_task.completed_at is None:
        db_task.completed_at = datetime.utcnow()
    elif task_update.status != TaskStatusEnum.FINISHED:
        db_task.completed_at = None
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    
    # Load relationships for response
    db_task = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(Task.id == db_task.id).first()
    
    # Create database notifications for task update
    try:
        from app.models.notification import NotificationType, NotificationPriority
        
        # Check if assignment changed
        assignment_changed = (task_update.assigned_to and 
                            task_update.assigned_to != db_task.assigned_to)
        
        if assignment_changed:
            # Create database notification for new assignee
            create_task_notification(
                db=db,
                user_id=db_task.assigned_to,
                task_title=db_task.title,
                notification_type=NotificationType.TASK_ASSIGNED,
                task_id=db_task.id,
                priority=NotificationPriority.HIGH if db_task.priority == "CRITICAL" else 
                        NotificationPriority.MEDIUM if db_task.priority == "HIGH" else 
                        NotificationPriority.LOW,
                additional_info=f"Reassigned by {current_user.name}"
            )
            print(f"Database reassignment notification created for user {db_task.assigned_to}")
        else:
            # Create database notification for task update
            create_task_notification(
                db=db,
                user_id=db_task.assigned_to,
                task_title=db_task.title,
                notification_type=NotificationType.TASK_UPDATED,
                task_id=db_task.id,
                priority=NotificationPriority.MEDIUM,
                additional_info=f"Updated by {current_user.name}"
            )
            print(f"Database update notification created for user {db_task.assigned_to}")
    except Exception as e:
        print(f"Error creating database notification: {e}")
        # Don't fail the main operation if notification fails

    # Send WebSocket notification for task update
    try:
        task_data = {
            "task_id": db_task.id,
            "title": db_task.title,
            "status": db_task.status,
            "priority": db_task.priority,
            "updated_by": current_user.name,
            "assignee_name": db_task.assignee.name,
            "creator_name": db_task.creator.name
        }
        
        # Check if assignment changed
        assignment_changed = (task_update.assigned_to and 
                            task_update.assigned_to != db_task.assigned_to)
        
        if assignment_changed:
            # Notify the new assignee
            send_notification_async(
                notification_type="task_reassigned",
                title="Task Reassigned",
                message=f"You have been assigned task '{db_task.title}' by {current_user.name}",
                target_user_id=db_task.assigned_to,
                task_data=task_data
            )
            
            # Notify the previous assignee if different
            if db_task.assigned_to != current_user.id:
                send_notification_async(
                    notification_type="task_reassigned",
                    title="Task Reassigned",
                    message=f"Task '{db_task.title}' has been reassigned by {current_user.name}",
                    target_user_id=db_task.assigned_to,
                    task_data=task_data
                )
        else:
            # General task update notification
            if db_task.assigned_to != current_user.id:
                send_notification_async(
                    notification_type="task_updated",
                    title="Task Updated",
                    message=f"Task '{db_task.title}' has been updated by {current_user.name}",
                    target_user_id=db_task.assigned_to,
                    task_data=task_data
                )
            
            if db_task.created_by != current_user.id:
                send_notification_async(
                    notification_type="task_updated",
                    title="Task Updated",
                    message=f"Task '{db_task.title}' has been updated by {current_user.name}",
                    target_user_id=db_task.created_by,
                    task_data=task_data
                )
                
    except Exception as e:
        print(f"Error sending task update notification: {e}")
    
    return db_task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Only allow creator or assigned user to delete
    if db_task.created_by != current_user.id and db_task.assigned_to != current_user.id:
        # You might want to add role-based permissions here
        pass
    
    db.delete(db_task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

# Task Log endpoints
@router.post("/{task_id}/logs", response_model=TaskLogOut)
def create_task_log(
    task_id: int,
    log: TaskLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a log entry for a task"""
    
    # Verify task exists
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Create log entry
    db_log = TaskLog(
        task_id=task_id,
        title=log.title,
        description=log.description,
        start_time=log.start_time,
        end_time=log.end_time
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log

@router.get("/{task_id}/logs", response_model=List[TaskLogOut])
def get_task_logs(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all log entries for a task"""
    
    # Verify task exists
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.desc()).all()
    return logs

# New hierarchy-based endpoints
@router.get("/assignable-users", response_model=List[dict])
def get_assignable_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users that can be assigned tasks by the current user"""
    hierarchy_manager = HierarchyManager(db)
    assignable_users = hierarchy_manager.get_assignable_users(current_user.id)
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "is_subordinate": hierarchy_manager.is_subordinate_of(user.id, current_user.id),
            "is_peer": (user.supervisor_id == current_user.supervisor_id and 
                       user.id != current_user.id and current_user.supervisor_id is not None)
        }
        for user in assignable_users
    ]

@router.get("/my-team-tasks", response_model=List[TaskOut])
def get_my_team_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks for current user's scope based on role"""
    hierarchy_manager = HierarchyManager(db)
    
    # Get user IDs that current user can view based on role
    viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
    
    tasks = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project),
        joinedload(Task.team),
        joinedload(Task.task_logs)
    ).filter(
        or_(
            Task.created_by.in_(viewable_user_ids),
            Task.assigned_to.in_(viewable_user_ids)
        )
    ).offset(skip).limit(limit).all()
    
    return tasks
