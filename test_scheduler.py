#!/usr/bin/env python3
"""
Test script for the task scheduler functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scheduler import task_scheduler
from app.database import get_db
from app.models import Task, User
from sqlalchemy.orm import Session

async def test_scheduler():
    """Test the scheduler functionality"""
    print("Testing Task Scheduler...")
    
    # Start the scheduler
    task_scheduler.start()
    print("✓ Scheduler started")
    
    # Get scheduler status
    status = await task_scheduler.get_scheduler_status()
    print(f"✓ Scheduler status: {status['status']}")
    print(f"✓ Active jobs: {len(status['jobs'])}")
    
    # Test manual trigger for due today check
    print("\nTesting due today check...")
    try:
        await task_scheduler.check_tasks_due_today()
        print("✓ Due today check completed")
    except Exception as e:
        print(f"✗ Due today check failed: {e}")
    
    # Test manual trigger for overdue check
    print("\nTesting overdue check...")
    try:
        await task_scheduler.check_overdue_tasks()
        print("✓ Overdue check completed")
    except Exception as e:
        print(f"✗ Overdue check failed: {e}")
    
    # Stop the scheduler
    task_scheduler.stop()
    print("✓ Scheduler stopped")

def test_database_connection():
    """Test database connection and query tasks"""
    print("\nTesting database connection...")
    try:
        db = next(get_db())
        
        # Get all tasks
        tasks = db.query(Task).all()
        print(f"✓ Found {len(tasks)} tasks in database")
        
        # Get tasks due today
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        tasks_due_today = db.query(Task).filter(
            Task.due_date >= start_of_day,
            Task.due_date <= end_of_day
        ).all()
        
        print(f"✓ Found {len(tasks_due_today)} tasks due today")
        
        # Get overdue tasks
        now = datetime.now()
        overdue_tasks = db.query(Task).filter(
            Task.due_date < now,
            Task.status.in_(['NEW', 'IN_PROGRESS', 'PENDING'])
        ).all()
        
        print(f"✓ Found {len(overdue_tasks)} overdue tasks")
        
        db.close()
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Task Scheduler Test")
    print("=" * 50)
    
    # Test database connection first
    test_database_connection()
    
    # Test scheduler
    asyncio.run(test_scheduler())
    
    print("\nTest completed!")
