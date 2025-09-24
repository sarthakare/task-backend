# Task Scheduler Documentation

## Overview

The Task Scheduler is a background service that automatically checks for tasks due today and overdue tasks, sending notifications to users via WebSocket and storing notifications in the database.

## Features

- **Automatic Task Due Today Reminders**: Checks every hour and at 9 AM daily for tasks due today
- **Overdue Task Notifications**: Checks every 2 hours for overdue tasks
- **WebSocket Notifications**: Real-time notifications sent to connected users
- **Database Notifications**: Persistent notifications stored in the database
- **Automatic Cleanup**: Removes old notifications (older than 30 days) daily at midnight

## Scheduler Jobs

### 1. Tasks Due Today Check
- **Frequency**: Every 2 minutes + Daily at 9 AM
- **Purpose**: Find tasks due today and send notifications
- **Target**: Users assigned to tasks due today
- **Notification Type**: `TASK_DUE_SOON`

### 2. Overdue Tasks Check
- **Frequency**: Every 5 minutes
- **Purpose**: Find overdue tasks and send urgent notifications
- **Target**: Users assigned to overdue tasks
- **Notification Type**: `TASK_OVERDUE`

### 3. Notification Cleanup
- **Frequency**: Daily at midnight
- **Purpose**: Remove notifications older than 30 days
- **Target**: All old notifications

## API Endpoints

### Get Scheduler Status
```
GET /scheduler/status
```
Returns the current status of the scheduler and information about scheduled jobs.

### Manual Triggers

#### Trigger Due Today Check
```
POST /scheduler/trigger/due-today
```
Manually trigger the due today task check.

#### Trigger Overdue Check
```
POST /scheduler/trigger/overdue
```
Manually trigger the overdue task check.

## WebSocket Notifications

The scheduler sends real-time notifications via WebSocket with the following structure:

```json
{
  "type": "task_notification",
  "notification_type": "task_due_today" | "task_overdue",
  "title": "Task Due Today" | "Task Overdue",
  "message": "Task 'Task Name' is due today at 14:30",
  "task_data": {
    "id": 123,
    "title": "Task Name",
    "due_date": "2024-01-15T14:30:00",
    "priority": "HIGH",
    "status": "IN_PROGRESS"
  },
  "timestamp": "2024-01-15T10:00:00"
}
```

## Database Notifications

Notifications are stored in the `notifications` table with the following structure:

- `user_id`: ID of the user to notify
- `title`: Notification title
- `message`: Notification message
- `notification_type`: Type of notification (`TASK_DUE_SOON`, `TASK_OVERDUE`)
- `priority`: Priority level (`HIGH`, `URGENT`)
- `related_entity_type`: "task"
- `related_entity_id`: Task ID
- `created_at`: Timestamp when notification was created

## Configuration

The scheduler is automatically started when the FastAPI application starts and stopped when the application shuts down.

### Job Scheduling
- **Due Today Check**: Every 2 minutes + Daily at 9 AM
- **Overdue Check**: Every 5 minutes
- **Cleanup**: Daily at midnight

## Testing

### Manual Testing
You can test the scheduler manually using the provided endpoints:

```bash
# Check scheduler status
curl http://localhost:8000/scheduler/status

# Trigger due today check
curl -X POST http://localhost:8000/scheduler/trigger/due-today

# Trigger overdue check
curl -X POST http://localhost:8000/scheduler/trigger/overdue
```

### Test Script
Run the test script to verify scheduler functionality:

```bash
cd task-backend
python test_scheduler.py
```

## Dependencies

The scheduler requires the following additional dependency:
- `APScheduler==3.10.4`

## Error Handling

The scheduler includes comprehensive error handling:
- Database connection errors are logged and don't stop the scheduler
- WebSocket notification failures are logged but don't affect database notifications
- Individual task notification failures don't stop processing of other tasks

## Logging

The scheduler uses Python's logging module with INFO level logging. All scheduler activities are logged, including:
- Job execution start/completion
- Number of tasks found
- Notification sending results
- Error conditions

## Monitoring

You can monitor the scheduler through:
1. **API Endpoint**: `/scheduler/status` - Get current status and job information
2. **Logs**: Check application logs for scheduler activity
3. **Database**: Check the `notifications` table for created notifications

## Troubleshooting

### Common Issues

1. **Scheduler not starting**: Check if APScheduler is installed
2. **No notifications sent**: Verify WebSocket connections and database connectivity
3. **Database errors**: Check database connection and table structure

### Debug Mode

Enable debug logging by setting the log level to DEBUG in the scheduler service.

## Future Enhancements

Potential improvements for the scheduler:
- Configurable notification intervals
- Email notifications in addition to WebSocket
- Task priority-based notification scheduling
- User preference settings for notification types
- Integration with external calendar systems
