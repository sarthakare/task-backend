# app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import csv
import io
import os
import tempfile
from pathlib import Path

from app.database import get_db
from app.models import User, Task, Project, Team, TaskLog
from app.models.task import TaskStatus, TaskPriority
from app.utils.auth import get_current_user
from app.utils.hierarchy import HierarchyManager

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/test")
async def test_reports_endpoint():
    """Test endpoint to verify reports router is working"""
    return {"message": "Reports router is working", "timestamp": datetime.utcnow().isoformat()}

@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("pdf", description="Export format: pdf, excel"),
    date_range: str = Query("last_30_days", description="Date range for the report"),
    include_charts: bool = Query(True, description="Include charts in the report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export analytics report in various formats"""
    
    try:
        # Get analytics data based on report type
        if report_type == "analytics":
            data = await get_analytics_data(db, current_user, date_range)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported report type: {report_type}"
            )
        
        # Generate file based on format
        if format.lower() == "excel":
            return await export_excel_report(data, report_type)
        elif format.lower() == "pdf":
            return await export_pdf_report(data, report_type)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}. Supported formats: pdf, excel"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )

async def get_analytics_data(db: Session, current_user: User, date_range: str) -> Dict[str, Any]:
    """Get comprehensive analytics data"""
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if date_range == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last_90_days":
            start_date = end_date - timedelta(days=90)
        elif date_range == "last_year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        hierarchy_manager = HierarchyManager(db)
        viewable_user_ids = hierarchy_manager.get_viewable_user_ids_by_role(current_user.id)
        
        # Fallback: if no viewable users, include current user
        if not viewable_user_ids:
            viewable_user_ids = [current_user.id]
            
    except Exception as e:
        print(f"Error in get_analytics_data setup: {e}")
        # Fallback to current user only
        viewable_user_ids = [current_user.id]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    # Get overview data with error handling
    try:
        overview = {
            "total_users": db.query(User).filter(User.id.in_(viewable_user_ids)).count(),
            "active_users": db.query(User).filter(
                User.id.in_(viewable_user_ids),
                User.is_active == True
            ).count(),
            "total_projects": db.query(Project).count(),
            "active_projects": db.query(Project).filter(Project.status == "active").count(),
            "total_tasks": db.query(Task).filter(
                or_(
                    Task.created_by.in_(viewable_user_ids),
                    Task.assigned_to.in_(viewable_user_ids)
                )
            ).count(),
            "completed_tasks": db.query(Task).filter(
                and_(
                    Task.status == TaskStatus.FINISHED,
                    or_(
                        Task.created_by.in_(viewable_user_ids),
                        Task.assigned_to.in_(viewable_user_ids)
                    )
                )
            ).count(),
            "overdue_tasks": db.query(Task).filter(
                and_(
                    Task.due_date < end_date,
                    ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED]),
                    or_(
                        Task.created_by.in_(viewable_user_ids),
                        Task.assigned_to.in_(viewable_user_ids)
                    )
                )
            ).count(),
        }
    except Exception as e:
        print(f"Error getting overview data: {e}")
        # Fallback overview data
        overview = {
            "total_users": 0,
            "active_users": 0,
            "total_projects": 0,
            "active_projects": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
        }
    
    # Get task status distribution with error handling
    try:
        task_status_data = []
        for status in TaskStatus:
            count = db.query(Task).filter(
                and_(
                    Task.status == status,
                    or_(
                        Task.created_by.in_(viewable_user_ids),
                        Task.assigned_to.in_(viewable_user_ids)
                    )
                )
            ).count()
            if count > 0:
                task_status_data.append({
                    "status": status.value,
                    "count": count
                })
    except Exception as e:
        print(f"Error getting task status data: {e}")
        task_status_data = []
    
    # Get user activity data (last 7 days) with error handling
    try:
        user_activity_data = []
        for i in range(7):
            date = end_date - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            tasks_created = db.query(Task).filter(
                and_(
                    Task.created_at >= date_start,
                    Task.created_at <= date_end,
                    Task.created_by.in_(viewable_user_ids)
                )
            ).count()
            
            tasks_completed = db.query(Task).filter(
                and_(
                    Task.updated_at >= date_start,
                    Task.updated_at <= date_end,
                    Task.status == TaskStatus.FINISHED,
                    or_(
                        Task.created_by.in_(viewable_user_ids),
                        Task.assigned_to.in_(viewable_user_ids)
                    )
                )
            ).count()
            
            user_activity_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "tasks_created": tasks_created,
                "tasks_completed": tasks_completed
            })
    except Exception as e:
        print(f"Error getting user activity data: {e}")
        user_activity_data = []
    
    # Get project progress data with error handling
    try:
        projects = db.query(Project).all()
        project_progress_data = []
        for project in projects[:10]:  # Limit to 10 projects
            project_tasks = db.query(Task).filter(Task.project_id == project.id).all()
            total_tasks = len(project_tasks)
            completed_tasks = len([t for t in project_tasks if t.status == TaskStatus.FINISHED])
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            project_progress_data.append({
                "project_name": project.name,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": round(progress_percentage, 1)
            })
    except Exception as e:
        print(f"Error getting project progress data: {e}")
        project_progress_data = []
    
    # Get team performance data with error handling
    try:
        teams = db.query(Team).all()
        team_performance_data = []
        for team in teams[:8]:  # Limit to 8 teams
            team_tasks = db.query(Task).filter(Task.team_id == team.id).all()
            total_team_tasks = len(team_tasks)
            completed_team_tasks = len([t for t in team_tasks if t.status == TaskStatus.FINISHED])
            efficiency = (completed_team_tasks / total_team_tasks * 100) if total_team_tasks > 0 else 0
            
            team_performance_data.append({
                "team_name": team.name,
                "total_tasks": total_team_tasks,
                "completed_tasks": completed_team_tasks,
                "efficiency": round(efficiency, 1)
            })
    except Exception as e:
        print(f"Error getting team performance data: {e}")
        team_performance_data = []
    
    return {
        "overview": overview,
        "task_status_data": task_status_data,
        "user_activity_data": user_activity_data,
        "project_progress_data": project_progress_data,
        "team_performance_data": team_performance_data,
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": date_range,
            "generated_by": current_user.name,
            "user_role": current_user.role
        }
    }


async def export_excel_report(data: Dict[str, Any], report_type: str):
    """Export report as Excel (returns CSV with .csv extension for Excel compatibility)"""
    # Create CSV content with Excel-like formatting
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write overview data
    writer.writerow(["Analytics Report", ""])
    writer.writerow(["Generated At", data["report_metadata"]["generated_at"]])
    writer.writerow(["Generated By", data["report_metadata"]["generated_by"]])
    writer.writerow(["Date Range", data["report_metadata"]["date_range"]])
    writer.writerow([])
    
    # Write overview metrics
    writer.writerow(["Overview Metrics"])
    overview = data["overview"]
    for key, value in overview.items():
        writer.writerow([key.replace("_", " ").title(), value])
    writer.writerow([])
    
    # Write task status data
    writer.writerow(["Task Status Distribution"])
    writer.writerow(["Status", "Count"])
    for item in data["task_status_data"]:
        writer.writerow([item["status"], item["count"]])
    writer.writerow([])
    
    # Write user activity data
    writer.writerow(["User Activity (Last 7 Days)"])
    writer.writerow(["Date", "Tasks Created", "Tasks Completed"])
    for item in data["user_activity_data"]:
        writer.writerow([item["date"], item["tasks_created"], item["tasks_completed"]])
    writer.writerow([])
    
    # Write project progress data
    writer.writerow(["Project Progress"])
    writer.writerow(["Project Name", "Total Tasks", "Completed Tasks", "Progress %"])
    for item in data["project_progress_data"]:
        writer.writerow([
            item["project_name"],
            item["total_tasks"],
            item["completed_tasks"],
            item["progress_percentage"]
        ])
    writer.writerow([])
    
    # Write team performance data
    writer.writerow(["Team Performance"])
    writer.writerow(["Team Name", "Total Tasks", "Completed Tasks", "Efficiency %"])
    for item in data["team_performance_data"]:
        writer.writerow([
            item["team_name"],
            item["total_tasks"],
            item["completed_tasks"],
            item["efficiency"]
        ])
    
    # Convert to bytes
    csv_content = output.getvalue()
    output.close()
    
    # Create temporary file with .csv extension (Excel can open CSV files)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(csv_content)
        temp_file_path = temp_file.name
    
    return FileResponse(
        path=temp_file_path,
        filename=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        media_type="text/csv"
    )

async def export_pdf_report(data: Dict[str, Any], report_type: str):
    """Export report as PDF (returns HTML that can be printed to PDF)"""
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .metric {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .metric-label {{ font-weight: bold; color: #007bff; }}
            .metric-value {{ font-size: 18px; color: #333; }}
            @media print {{ body {{ margin: 0; }} }}
        </style>
    </head>
    <body>
        <h1>Analytics Report</h1>
        <p><strong>Generated:</strong> {data["report_metadata"]["generated_at"]}</p>
        <p><strong>Generated By:</strong> {data["report_metadata"]["generated_by"]}</p>
        <p><strong>Date Range:</strong> {data["report_metadata"]["date_range"]}</p>
        
        <h2>Overview Metrics</h2>
        <div class="metric">
            <div class="metric-label">Total Users:</div>
            <div class="metric-value">{data["overview"]["total_users"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Active Users:</div>
            <div class="metric-value">{data["overview"]["active_users"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Projects:</div>
            <div class="metric-value">{data["overview"]["total_projects"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Active Projects:</div>
            <div class="metric-value">{data["overview"]["active_projects"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Tasks:</div>
            <div class="metric-value">{data["overview"]["total_tasks"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Completed Tasks:</div>
            <div class="metric-value">{data["overview"]["completed_tasks"]}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Overdue Tasks:</div>
            <div class="metric-value">{data["overview"]["overdue_tasks"]}</div>
        </div>
        
        <h2>Task Status Distribution</h2>
        <table>
            <tr><th>Status</th><th>Count</th></tr>
    """
    
    for item in data["task_status_data"]:
        html_content += f"<tr><td>{item['status']}</td><td>{item['count']}</td></tr>"
    
    html_content += """
        </table>
        
        <h2>User Activity (Last 7 Days)</h2>
        <table>
            <tr><th>Date</th><th>Tasks Created</th><th>Tasks Completed</th></tr>
    """
    
    for item in data["user_activity_data"]:
        html_content += f"<tr><td>{item['date']}</td><td>{item['tasks_created']}</td><td>{item['tasks_completed']}</td></tr>"
    
    html_content += """
        </table>
        
        <h2>Project Progress</h2>
        <table>
            <tr><th>Project Name</th><th>Total Tasks</th><th>Completed Tasks</th><th>Progress %</th></tr>
    """
    
    for item in data["project_progress_data"]:
        html_content += f"<tr><td>{item['project_name']}</td><td>{item['total_tasks']}</td><td>{item['completed_tasks']}</td><td>{item['progress_percentage']}%</td></tr>"
    
    html_content += """
        </table>
        
        <h2>Team Performance</h2>
        <table>
            <tr><th>Team Name</th><th>Total Tasks</th><th>Completed Tasks</th><th>Efficiency %</th></tr>
    """
    
    for item in data["team_performance_data"]:
        html_content += f"<tr><td>{item['team_name']}</td><td>{item['total_tasks']}</td><td>{item['completed_tasks']}</td><td>{item['efficiency']}%</td></tr>"
    
    html_content += """
        </table>
        
        <script>
            // Auto-print when opened
            window.onload = function() {
                setTimeout(function() {
                    window.print();
                }, 1000);
            };
        </script>
    </body>
    </html>
    """
    
    # Create temporary file with .html extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(html_content)
        temp_file_path = temp_file.name
    
    return FileResponse(
        path=temp_file_path,
        filename=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        media_type="text/html"
    )

@router.get("/user/{user_id}")
async def get_user_performance_report(
    user_id: int,
    date_range: str = Query("last_30_days", description="Date range for the report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user performance report"""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    if date_range == "last_7_days":
        start_date = end_date - timedelta(days=7)
    elif date_range == "last_30_days":
        start_date = end_date - timedelta(days=30)
    elif date_range == "last_90_days":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get user's tasks
    user_tasks = db.query(Task).filter(
        and_(
            Task.assigned_to == user_id,
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    ).all()
    
    # Calculate metrics
    total_tasks = len(user_tasks)
    completed_tasks = len([t for t in user_tasks if t.status == TaskStatus.FINISHED])
    overdue_tasks = len([t for t in user_tasks if t.due_date < end_date and t.status != TaskStatus.FINISHED])
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department
        },
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round(completion_rate, 1)
        },
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

@router.get("/team/{team_id}")
async def get_team_performance_report(
    team_id: int,
    date_range: str = Query("last_30_days", description="Date range for the report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team performance report"""
    
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    if date_range == "last_7_days":
        start_date = end_date - timedelta(days=7)
    elif date_range == "last_30_days":
        start_date = end_date - timedelta(days=30)
    elif date_range == "last_90_days":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get team's tasks
    team_tasks = db.query(Task).filter(
        and_(
            Task.team_id == team_id,
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    ).all()
    
    # Calculate metrics
    total_tasks = len(team_tasks)
    completed_tasks = len([t for t in team_tasks if t.status == TaskStatus.FINISHED])
    overdue_tasks = len([t for t in team_tasks if t.due_date < end_date and t.status != TaskStatus.FINISHED])
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get team members performance
    members_performance = []
    for member in team.members:
        member_tasks = [t for t in team_tasks if t.assigned_to == member.id]
        member_completed = len([t for t in member_tasks if t.status == TaskStatus.FINISHED])
        member_completion_rate = (member_completed / len(member_tasks) * 100) if member_tasks else 0
        
        members_performance.append({
            "user_id": member.id,
            "name": member.name,
            "total_tasks": len(member_tasks),
            "completed_tasks": member_completed,
            "completion_rate": round(member_completion_rate, 1)
        })
    
    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "department": team.department,
            "leader": team.leader.name if team.leader else None
        },
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round(completion_rate, 1)
        },
        "members_performance": members_performance,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

@router.get("/system")
async def get_system_stats_report(
    date_range: str = Query("last_30_days", description="Date range for the report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system-wide statistics report"""
    
    # Calculate date range
    end_date = datetime.utcnow()
    if date_range == "last_7_days":
        start_date = end_date - timedelta(days=7)
    elif date_range == "last_30_days":
        start_date = end_date - timedelta(days=30)
    elif date_range == "last_90_days":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get system-wide metrics
    total_users = db.query(User).filter(User.role != "ADMIN").count()
    active_users = db.query(User).filter(
        User.is_active == True,
        User.role != "ADMIN"
    ).count()
    
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()
    
    total_tasks = db.query(Task).filter(
        Task.created_at >= start_date,
        Task.created_at <= end_date
    ).count()
    
    completed_tasks = db.query(Task).filter(
        and_(
            Task.status == TaskStatus.FINISHED,
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
    ).count()
    
    overdue_tasks = db.query(Task).filter(
        and_(
            Task.due_date < end_date,
            ~Task.status.in_([TaskStatus.FINISHED, TaskStatus.CANCELLED])
        )
    ).count()
    
    return {
        "system_metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks
        },
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }
