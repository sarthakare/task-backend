# app/services/scheduler.py
"""
Scheduler service for task due today reminders and other periodic tasks
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging

from app.database import get_db
from app.models import Task, User, Notification, NotificationType, NotificationPriority
from app.utils.notifications import create_task_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Scheduler for task-related notifications and reminders"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            # Schedule task due today check every 30 minutes
            self.scheduler.add_job(
                self.check_tasks_due_today,
                trigger=IntervalTrigger(minutes=2),
                id='check_tasks_due_today',
                name='Check Tasks Due Today',
                replace_existing=True
            )
            
            # Schedule task due today check at 9 AM every day
            self.scheduler.add_job(
                self.check_tasks_due_today,
                trigger=CronTrigger(hour=9, minute=0),
                id='daily_tasks_due_today',
                name='Daily Tasks Due Today Check',
                replace_existing=True
            )
            
            # Schedule task due tomorrow check at 5 PM every day
            self.scheduler.add_job(
                self.check_tasks_due_tomorrow,
                trigger=CronTrigger(hour=17, minute=0),
                id='daily_tasks_due_tomorrow',
                name='Daily Tasks Due Tomorrow Check',
                replace_existing=True
            )
            
            # Schedule overdue task check every 5 minutes
            self.scheduler.add_job(
                self.check_overdue_tasks,
                trigger=IntervalTrigger(minutes=5),
                id='check_overdue_tasks',
                name='Check Overdue Tasks',
                replace_existing=True
            )
            
            # Schedule cleanup of old notifications daily at midnight
            self.scheduler.add_job(
                self.cleanup_old_notifications,
                trigger=CronTrigger(hour=0, minute=0),
                id='cleanup_notifications',
                name='Cleanup Old Notifications',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started successfully")
            
            # Run initial check
            asyncio.create_task(self.check_tasks_due_today())
            
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    async def check_tasks_due_today(self):
        """Check for tasks due today and send notifications"""
        try:
            logger.info("Checking for tasks due today...")
            
            # Get database session
            db = next(get_db())
            
            # Get current date (start and end of today)
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # Find tasks due today that are not completed
            tasks_due_today = db.query(Task).filter(
                and_(
                    Task.due_date >= start_of_day,
                    Task.due_date <= end_of_day,
                    Task.status.in_(['NEW', 'IN_PROGRESS', 'PENDING'])  # Not completed tasks
                )
            ).all()
            
            logger.info(f"Found {len(tasks_due_today)} tasks due today")
            
            # Send notifications for each task
            for task in tasks_due_today:
                await self.send_task_due_notification(db, task)
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error checking tasks due today: {e}")
            import traceback
            traceback.print_exc()
    
    async def check_overdue_tasks(self):
        """Check for overdue tasks and send notifications"""
        try:
            logger.info("Checking for overdue tasks...")
            
            # Get database session
            db = next(get_db())
            
            # Find overdue tasks
            now = datetime.now()
            overdue_tasks = db.query(Task).filter(
                and_(
                    Task.due_date < now,
                    Task.status.in_(['NEW', 'IN_PROGRESS', 'PENDING'])  # Not completed tasks
                )
            ).all()
            
            logger.info(f"Found {len(overdue_tasks)} overdue tasks")
            
            # Send notifications for each overdue task
            for task in overdue_tasks:
                await self.send_overdue_task_notification(db, task)
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error checking overdue tasks: {e}")
            import traceback
            traceback.print_exc()
    
    async def check_tasks_due_tomorrow(self):
        """Check for tasks due tomorrow and send notifications"""
        try:
            logger.info("Checking for tasks due tomorrow...")
            
            # Get database session
            db = next(get_db())
            
            # Get tomorrow's date (start and end of tomorrow)
            tomorrow = datetime.now().date() + timedelta(days=1)
            start_of_tomorrow = datetime.combine(tomorrow, datetime.min.time())
            end_of_tomorrow = datetime.combine(tomorrow, datetime.max.time())
            
            # Find tasks due tomorrow that are not completed
            tasks_due_tomorrow = db.query(Task).filter(
                and_(
                    Task.due_date >= start_of_tomorrow,
                    Task.due_date <= end_of_tomorrow,
                    Task.status.in_(['NEW', 'IN_PROGRESS', 'PENDING'])  # Not completed tasks
                )
            ).all()
            
            logger.info(f"Found {len(tasks_due_tomorrow)} tasks due tomorrow")
            
            # Send notifications for each task
            for task in tasks_due_tomorrow:
                await self.send_task_due_tomorrow_notification(db, task)
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error checking tasks due tomorrow: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_task_due_notification(self, db: Session, task: Task):
        """Send notification for task due today"""
        try:
            # Check if notification already exists for this task today
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            existing_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == task.assigned_to,
                    Notification.related_entity_type == "task",
                    Notification.related_entity_id == task.id,
                    Notification.notification_type == NotificationType.TASK_DUE_SOON,
                    Notification.created_at >= start_of_day,
                    Notification.created_at <= end_of_day
                )
            ).first()
            
            if existing_notification:
                logger.info(f"Notification already exists for task {task.id} today, skipping")
                return
            
            # Create database notification
            notification = create_task_notification(
                db=db,
                user_id=task.assigned_to,
                task_title=task.title,
                notification_type=NotificationType.TASK_DUE_SOON,
                task_id=task.id,
                priority=NotificationPriority.HIGH,
                additional_info=f"Due today at {task.due_date.strftime('%H:%M')}"
            )
            
            # Send WebSocket notification
            await self.send_websocket_notification(
                user_id=task.assigned_to,
                notification_type="task_due_today",
                title="Task Due Today",
                message=f"Task '{task.title}' is due today at {task.due_date.strftime('%H:%M')}",
                task_data={
                    "id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status)
                }
            )
            
            logger.info(f"Sent due today notification for task {task.id} to user {task.assigned_to}")
            
        except Exception as e:
            logger.error(f"Error sending task due notification: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_overdue_task_notification(self, db: Session, task: Task):
        """Send notification for overdue task"""
        try:
            # Check if notification already exists for this task today
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            existing_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == task.assigned_to,
                    Notification.related_entity_type == "task",
                    Notification.related_entity_id == task.id,
                    Notification.notification_type == NotificationType.TASK_OVERDUE,
                    Notification.created_at >= start_of_day,
                    Notification.created_at <= end_of_day
                )
            ).first()
            
            if existing_notification:
                logger.info(f"Overdue notification already exists for task {task.id} today, skipping")
                return
            
            # Create database notification
            notification = create_task_notification(
                db=db,
                user_id=task.assigned_to,
                task_title=task.title,
                notification_type=NotificationType.TASK_OVERDUE,
                task_id=task.id,
                priority=NotificationPriority.URGENT,
                additional_info=f"Overdue since {task.due_date.strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Send WebSocket notification
            await self.send_websocket_notification(
                user_id=task.assigned_to,
                notification_type="task_overdue",
                title="Task Overdue",
                message=f"Task '{task.title}' is overdue since {task.due_date.strftime('%Y-%m-%d %H:%M')}",
                task_data={
                    "id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status)
                }
            )
            
            logger.info(f"Sent overdue notification for task {task.id} to user {task.assigned_to}")
            
        except Exception as e:
            logger.error(f"Error sending overdue task notification: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_task_due_tomorrow_notification(self, db: Session, task: Task):
        """Send notification for task due tomorrow"""
        try:
            # Check if notification already exists for this task today
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            existing_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == task.assigned_to,
                    Notification.related_entity_type == "task",
                    Notification.related_entity_id == task.id,
                    Notification.notification_type == NotificationType.TASK_DUE_SOON,
                    Notification.created_at >= start_of_day,
                    Notification.created_at <= end_of_day
                )
            ).first()
            
            if existing_notification:
                logger.info(f"Tomorrow notification already exists for task {task.id} today, skipping")
                return
            
            # Create database notification
            notification = create_task_notification(
                db=db,
                user_id=task.assigned_to,
                task_title=task.title,
                notification_type=NotificationType.TASK_DUE_SOON,
                task_id=task.id,
                priority=NotificationPriority.MEDIUM,
                additional_info=f"Due tomorrow at {task.due_date.strftime('%H:%M')}"
            )
            
            # Send WebSocket notification
            await self.send_websocket_notification(
                user_id=task.assigned_to,
                notification_type="task_due_tomorrow",
                title="Task Due Tomorrow",
                message=f"Task '{task.title}' is due tomorrow at {task.due_date.strftime('%H:%M')}",
                task_data={
                    "id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status)
                }
            )
            
            logger.info(f"Sent due tomorrow notification for task {task.id} to user {task.assigned_to}")
            
        except Exception as e:
            logger.error(f"Error sending task due tomorrow notification: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_websocket_notification(
        self, 
        user_id: int, 
        notification_type: str, 
        title: str, 
        message: str, 
        task_data: Dict[str, Any] = None
    ):
        """Send WebSocket notification to user"""
        try:
            # Import here to avoid circular imports
            from main import send_to_user, active_connections
            import json
            
            notification_data = {
                "type": "task_notification",
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "task_data": task_data or {},
                "timestamp": datetime.now().isoformat()
            }
            
            json_message = json.dumps(notification_data)
            
            # Send to user if they're connected
            if user_id in active_connections:
                await send_to_user(user_id, json_message)
                logger.info(f"Sent WebSocket notification to user {user_id}")
            else:
                logger.info(f"User {user_id} not connected, notification saved to database only")
                
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
            import traceback
            traceback.print_exc()
    
    async def cleanup_old_notifications(self):
        """Clean up old notifications"""
        try:
            logger.info("Cleaning up old notifications...")
            
            db = next(get_db())
            
            # Delete notifications older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            old_notifications = db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).all()
            
            count = len(old_notifications)
            for notification in old_notifications:
                db.delete(notification)
            
            db.commit()
            db.close()
            
            logger.info(f"Cleaned up {count} old notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
            import traceback
            traceback.print_exc()
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and job information"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }

# Global scheduler instance
task_scheduler = TaskScheduler()
