"""
Demo Tasks Data for Task Manager Application
Creates realistic tasks assigned to different users and teams across various projects
"""

from datetime import datetime, timedelta
from app.schemas.task import TaskCreate, TaskStatus, TaskPriority

# Demo Tasks Data
# Structure: Task Title, Description, Project ID, Team ID, Assigned To, Status, Priority, Start Date, Due Date, Follow-up Date
DEMO_TASKS = [
    # CUSTOMER PORTAL REDESIGN PROJECT TASKS
    {
        "title": "Design new user interface mockups",
        "description": "Create wireframes and mockups for the redesigned customer portal homepage and navigation",
        "project_id": 1,  # Customer Portal Redesign
        "team_id": 1,  # Frontend Development Team
        "assigned_to": 6,  # Alex Thompson - Frontend Developer
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=25),
        "due_date": datetime.now() + timedelta(days=5),
        "follow_up_date": datetime.now() + timedelta(days=2)
    },
    {
        "title": "Implement responsive navigation component",
        "description": "Develop responsive navigation component with mobile-first approach",
        "project_id": 1,
        "team_id": 1,
        "assigned_to": 6,  # Alex Thompson
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=3),
        "due_date": datetime.now() + timedelta(days=15),
        "follow_up_date": datetime.now() + timedelta(days=10)
    },
    {
        "title": "Design database schema for user preferences",
        "description": "Create database schema to store user preferences and customization settings",
        "project_id": 1,
        "team_id": 2,  # Backend Development Team
        "assigned_to": 7,  # Jessica Liu - Backend Developer
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=1),
        "due_date": datetime.now() + timedelta(days=10),
        "follow_up_date": datetime.now() + timedelta(days=7)
    },
    {
        "title": "Create customer portal marketing content",
        "description": "Develop marketing content highlighting new portal features and benefits",
        "project_id": 1,
        "team_id": 4,  # Content Marketing Team
        "assigned_to": 13,  # Rachel Brown - Content Writer
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=20),
        "follow_up_date": datetime.now() + timedelta(days=15)
    },
    
    # Q4 SALES CAMPAIGN TASKS
    {
        "title": "Develop email marketing campaign",
        "description": "Create email sequences for Q4 sales campaign targeting different customer segments",
        "project_id": 2,  # Q4 Sales Campaign Launch
        "team_id": 3,  # Digital Marketing Team
        "assigned_to": 12,  # Chris Martinez - Digital Marketing Specialist
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=10),
        "due_date": datetime.now() + timedelta(days=5),
        "follow_up_date": datetime.now() + timedelta(days=2)
    },
    {
        "title": "Prepare sales presentation materials",
        "description": "Create comprehensive sales presentation materials for Q4 product launches",
        "project_id": 2,
        "team_id": 14,  # Enterprise Sales Team
        "assigned_to": 37,  # Steven Perez - Enterprise Sales Representative
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now(),
        "due_date": datetime.now() + timedelta(days=7),
        "follow_up_date": datetime.now() + timedelta(days=4)
    },
    {
        "title": "Create social media content calendar",
        "description": "Develop social media content calendar for Q4 campaign across all platforms",
        "project_id": 2,
        "team_id": 4,  # Content Marketing Team
        "assigned_to": 13,  # Rachel Brown
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=2),
        "due_date": datetime.now() + timedelta(days=12),
        "follow_up_date": datetime.now() + timedelta(days=8)
    },
    
    # EMPLOYEE PERFORMANCE MANAGEMENT SYSTEM TASKS
    {
        "title": "Design performance review workflow",
        "description": "Create user flow and wireframes for the performance review process",
        "project_id": 3,  # Employee Performance Management System
        "team_id": 1,  # Frontend Development Team
        "assigned_to": 6,  # Alex Thompson
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=40),
        "due_date": datetime.now() + timedelta(days=10),
        "follow_up_date": datetime.now() + timedelta(days=5)
    },
    {
        "title": "Implement goal tracking API",
        "description": "Develop REST API endpoints for goal creation, tracking, and updates",
        "project_id": 3,
        "team_id": 2,  # Backend Development Team
        "assigned_to": 7,  # Jessica Liu
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=25),
        "follow_up_date": datetime.now() + timedelta(days=15)
    },
    {
        "title": "Conduct user requirements gathering",
        "description": "Interview HR team and employees to gather requirements for performance system",
        "project_id": 3,
        "team_id": 7,  # Employee Relations Team
        "assigned_to": 18,  # Stephanie Jones - HR Specialist
        "status": TaskStatus.FINISHED,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=50),
        "due_date": datetime.now() - timedelta(days=20),
        "follow_up_date": datetime.now() - timedelta(days=15)
    },
    
    # MICROSERVICES ARCHITECTURE MIGRATION TASKS
    {
        "title": "Design microservices architecture",
        "description": "Create detailed architecture diagram and service breakdown for migration",
        "project_id": 5,  # Microservices Architecture Migration
        "team_id": 2,  # Backend Development Team
        "assigned_to": 4,  # Emily Rodriguez - Backend Team Lead
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.CRITICAL,
        "start_date": datetime.now() - timedelta(days=55),
        "due_date": datetime.now() + timedelta(days=5),
        "follow_up_date": datetime.now() + timedelta(days=2)
    },
    {
        "title": "Set up container orchestration",
        "description": "Configure Kubernetes cluster and container orchestration for microservices",
        "project_id": 5,
        "team_id": 3,  # DevOps Team
        "assigned_to": 8,  # Ryan O'Connor - DevOps Engineer
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=3),
        "due_date": datetime.now() + timedelta(days=20),
        "follow_up_date": datetime.now() + timedelta(days=12)
    },
    {
        "title": "Implement API gateway",
        "description": "Develop API gateway to manage microservices communication and routing",
        "project_id": 5,
        "team_id": 2,  # Backend Development Team
        "assigned_to": 7,  # Jessica Liu
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=8),
        "due_date": datetime.now() + timedelta(days=30),
        "follow_up_date": datetime.now() + timedelta(days=20)
    },
    
    # MOBILE APP DEVELOPMENT TASKS
    {
        "title": "Create mobile app wireframes",
        "description": "Design wireframes for iOS and Android mobile applications",
        "project_id": 6,  # Mobile App Development
        "team_id": 1,  # Frontend Development Team
        "assigned_to": 6,  # Alex Thompson
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=25),
        "follow_up_date": datetime.now() + timedelta(days=15)
    },
    {
        "title": "Set up mobile development environment",
        "description": "Configure development environment for React Native mobile app development",
        "project_id": 6,
        "team_id": 1,  # Frontend Development Team
        "assigned_to": 6,  # Alex Thompson
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=2),
        "due_date": datetime.now() + timedelta(days=12),
        "follow_up_date": datetime.now() + timedelta(days=8)
    },
    
    # BRAND IDENTITY REFRESH TASKS
    {
        "title": "Design new company logo",
        "description": "Create new company logo and brand mark variations for different applications",
        "project_id": 7,  # Brand Identity Refresh
        "team_id": 4,  # Content Marketing Team
        "assigned_to": 11,  # Amanda Garcia - Content Marketing Team Lead
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=20),
        "due_date": datetime.now() + timedelta(days=3),
        "follow_up_date": datetime.now() + timedelta(days=1)
    },
    {
        "title": "Update marketing materials with new branding",
        "description": "Apply new brand identity to all existing marketing materials and templates",
        "project_id": 7,
        "team_id": 4,  # Content Marketing Team
        "assigned_to": 13,  # Rachel Brown
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=25),
        "follow_up_date": datetime.now() + timedelta(days=15)
    },
    
    # FINANCIAL REPORTING AUTOMATION TASKS
    {
        "title": "Design automated reporting dashboard",
        "description": "Create wireframes and specifications for automated financial reporting dashboard",
        "project_id": 4,  # Financial Reporting Automation
        "team_id": 1,  # Frontend Development Team
        "assigned_to": 6,  # Alex Thompson
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=3),
        "due_date": datetime.now() + timedelta(days=18),
        "follow_up_date": datetime.now() + timedelta(days=12)
    },
    {
        "title": "Develop financial data processing pipeline",
        "description": "Create automated pipeline to process and aggregate financial data for reporting",
        "project_id": 4,
        "team_id": 2,  # Backend Development Team
        "assigned_to": 7,  # Jessica Liu
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=25),
        "follow_up_date": datetime.now() + timedelta(days=15)
    },
    {
        "title": "Validate financial data accuracy",
        "description": "Review and validate accuracy of automated financial data processing",
        "project_id": 4,
        "team_id": 8,  # Accounting Team
        "assigned_to": 22,  # Ashley Hall - Accountant
        "status": TaskStatus.NEW,
        "priority": TaskPriority.CRITICAL,
        "start_date": datetime.now() + timedelta(days=20),
        "due_date": datetime.now() + timedelta(days=35),
        "follow_up_date": datetime.now() + timedelta(days=28)
    },
    
    # HR AND OPERATIONS TASKS
    {
        "title": "Review remote work policy draft",
        "description": "Review and provide feedback on remote work policy implementation draft",
        "project_id": 9,  # Remote Work Policy Implementation
        "team_id": 7,  # Employee Relations Team
        "assigned_to": 18,  # Stephanie Jones
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() - timedelta(days=35),
        "due_date": datetime.now() + timedelta(days=5),
        "follow_up_date": datetime.now() + timedelta(days=2)
    },
    {
        "title": "Conduct process improvement analysis",
        "description": "Analyze current operational processes and identify improvement opportunities",
        "project_id": 13,  # Process Standardization Initiative
        "team_id": 10,  # Process Improvement Team
        "assigned_to": 27,  # Christopher Lopez - Process Analyst
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() - timedelta(days=60),
        "due_date": datetime.now() + timedelta(days=10),
        "follow_up_date": datetime.now() + timedelta(days=5)
    },
    
    # IT AND SECURITY TASKS
    {
        "title": "Migrate database to cloud",
        "description": "Migrate production database to cloud infrastructure with minimal downtime",
        "project_id": 15,  # Cloud Infrastructure Migration
        "team_id": 12,  # Infrastructure Team
        "assigned_to": 32,  # Catherine Baker - System Administrator
        "status": TaskStatus.NEW,
        "priority": TaskPriority.CRITICAL,
        "start_date": datetime.now() + timedelta(days=10),
        "due_date": datetime.now() + timedelta(days=25),
        "follow_up_date": datetime.now() + timedelta(days=18)
    },
    {
        "title": "Implement multi-factor authentication",
        "description": "Deploy multi-factor authentication across all company systems and applications",
        "project_id": 16,  # Cybersecurity Enhancement
        "team_id": 13,  # Security Team
        "assigned_to": 33,  # Jonathan Gonzalez - Security Specialist
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() + timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=20),
        "follow_up_date": datetime.now() + timedelta(days=12)
    },
    
    # SALES TASKS
    {
        "title": "Configure CRM system integration",
        "description": "Set up and configure CRM system integration with existing sales tools",
        "project_id": 17,  # CRM System Integration
        "team_id": 14,  # Enterprise Sales Team
        "assigned_to": 37,  # Steven Perez
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "start_date": datetime.now() - timedelta(days=20),
        "due_date": datetime.now() + timedelta(days=5),
        "follow_up_date": datetime.now() + timedelta(days=2)
    },
    {
        "title": "Train sales team on CRM usage",
        "description": "Conduct training sessions for sales team on new CRM system features and workflows",
        "project_id": 17,
        "team_id": 14,  # Enterprise Sales Team
        "assigned_to": 35,  # Mark Carter - Enterprise Sales Team Lead
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() + timedelta(days=8),
        "due_date": datetime.now() + timedelta(days=18),
        "follow_up_date": datetime.now() + timedelta(days=13)
    },
    
    # OVERDUE TASKS
    {
        "title": "Complete API documentation",
        "description": "Finalize comprehensive API documentation for all endpoints",
        "project_id": 5,  # Microservices Architecture Migration
        "team_id": 2,  # Backend Development Team
        "assigned_to": 7,  # Jessica Liu
        "status": TaskStatus.PENDING,
        "priority": TaskPriority.MEDIUM,
        "start_date": datetime.now() - timedelta(days=40),
        "due_date": datetime.now() - timedelta(days=5),
        "follow_up_date": datetime.now() - timedelta(days=2)
    },
    {
        "title": "Update employee handbook policies",
        "description": "Update employee handbook with latest policy changes and procedures",
        "project_id": 9,  # Remote Work Policy Implementation
        "team_id": 7,  # Employee Relations Team
        "assigned_to": 18,  # Stephanie Jones
        "status": TaskStatus.PENDING,
        "priority": TaskPriority.LOW,
        "start_date": datetime.now() - timedelta(days=25),
        "due_date": datetime.now() - timedelta(days=3),
        "follow_up_date": datetime.now() - timedelta(days=1)
    }
]

def get_demo_tasks():
    """Return list of TaskCreate objects for demo tasks"""
    return [TaskCreate(**task_data) for task_data in DEMO_TASKS]

def get_tasks_by_status():
    """Return tasks grouped by status"""
    status_groups = {}
    for task_data in DEMO_TASKS:
        status = task_data["status"]
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(task_data)
    return status_groups

def get_tasks_by_priority():
    """Return tasks grouped by priority"""
    priority_groups = {}
    for task_data in DEMO_TASKS:
        priority = task_data["priority"]
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(task_data)
    return priority_groups

def get_tasks_by_project():
    """Return tasks grouped by project"""
    project_groups = {}
    for task_data in DEMO_TASKS:
        project_id = task_data["project_id"]
        if project_id not in project_groups:
            project_groups[project_id] = []
        project_groups[project_id].append(task_data)
    return project_groups

def get_overdue_tasks():
    """Return tasks that are overdue"""
    overdue = []
    for task_data in DEMO_TASKS:
        if task_data["due_date"] < datetime.now() and task_data["status"] not in [TaskStatus.FINISHED, TaskStatus.CANCELLED]:
            overdue.append(task_data)
    return overdue

if __name__ == "__main__":
    print("Demo Tasks Data")
    print("===============")
    print(f"Total Tasks: {len(DEMO_TASKS)}")
    
    print("\nBy Status:")
    status_tasks = get_tasks_by_status()
    for status, tasks in status_tasks.items():
        print(f"  {status.value}: {len(tasks)} tasks")
    
    print("\nBy Priority:")
    priority_tasks = get_tasks_by_priority()
    for priority, tasks in priority_tasks.items():
        print(f"  {priority.value}: {len(tasks)} tasks")
    
    print("\nOverdue Tasks:")
    overdue = get_overdue_tasks()
    for task in overdue:
        days_overdue = (datetime.now() - task['due_date']).days
        print(f"  - {task['title']} ({days_overdue} days overdue)")
    
    print("\nTasks by Project:")
    project_tasks = get_tasks_by_project()
    for project_id, tasks in project_tasks.items():
        print(f"  Project {project_id}: {len(tasks)} tasks")
