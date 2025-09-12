"""
Demo Projects Data for Task Manager Application
Creates realistic projects across different departments with appropriate managers and teams
"""

from datetime import datetime, timedelta
from app.schemas.project import ProjectCreate

# Demo Projects Data
# Structure: Project Name, Description, Manager ID, Assigned Team IDs, Start Date, End Date, Status
DEMO_PROJECTS = [
    # CROSS-DEPARTMENT PROJECTS
    {
        "name": "Customer Portal Redesign",
        "description": "Complete redesign and modernization of the customer portal with improved UX and new features",
        "manager_id": 3,  # Rajesh Kumar - Engineering Manager
        "assigned_teams": [1, 2, 3],  # Frontend Team, Backend Team, Digital Marketing
        "start_date": datetime.now() - timedelta(days=30),
        "end_date": datetime.now() + timedelta(days=60),
        "status": "active"
    },
    {
        "name": "Q4 Sales Campaign Launch",
        "description": "Launch comprehensive sales campaign for Q4 with new product features and marketing materials",
        "manager_id": 12,  # Meera Joshi - Sales Manager
        "assigned_teams": [3, 8, 9],  # Digital Marketing, Enterprise Sales, SMB Sales
        "start_date": datetime.now() - timedelta(days=15),
        "end_date": datetime.now() + timedelta(days=75),
        "status": "active"
    },
    {
        "name": "Employee Performance Management System",
        "description": "Implement new digital performance management system with goal tracking and reviews",
        "manager_id": 17,  # Vijay Menon - HR Manager
        "assigned_teams": [1, 2, 4],  # Frontend Team, Backend Team, HR Operations Team
        "start_date": datetime.now() - timedelta(days=45),
        "end_date": datetime.now() + timedelta(days=90),
        "status": "active"
    },
    {
        "name": "Financial Reporting Automation",
        "description": "Automate monthly and quarterly financial reporting processes with real-time dashboards",
        "manager_id": 21,  # Srinivas Rao - Finance Manager
        "assigned_teams": [1, 2, 5],  # Frontend Team, Backend Team, Finance Operations Team
        "start_date": datetime.now() - timedelta(days=20),
        "end_date": datetime.now() + timedelta(days=45),
        "status": "active"
    },
    
    # ENGINEERING PROJECTS
    {
        "name": "Microservices Architecture Migration",
        "description": "Migrate monolithic application to microservices architecture for better scalability",
        "manager_id": 3,  # Rajesh Kumar - Engineering Manager
        "assigned_teams": [1, 2],  # Frontend Team, Backend Team
        "start_date": datetime.now() - timedelta(days=60),
        "end_date": datetime.now() + timedelta(days=120),
        "status": "active"
    },
    {
        "name": "Mobile App Development",
        "description": "Develop native mobile applications for iOS and Android platforms",
        "manager_id": 3,  # Rajesh Kumar - Engineering Manager
        "assigned_teams": [1, 2],  # Frontend Team, Backend Team
        "start_date": datetime.now() - timedelta(days=10),
        "end_date": datetime.now() + timedelta(days=150),
        "status": "active"
    },
    
    # MARKETING PROJECTS
    {
        "name": "Brand Identity Refresh",
        "description": "Update company branding, logo, and visual identity across all marketing materials",
        "manager_id": 8,  # Anita Desai - Marketing Manager
        "assigned_teams": [3],  # Digital Marketing Team
        "start_date": datetime.now() - timedelta(days=25),
        "end_date": datetime.now() + timedelta(days=30),
        "status": "active"
    },
    {
        "name": "SEO Optimization Initiative",
        "description": "Comprehensive SEO audit and optimization for all company websites and content",
        "manager_id": 8,  # Anita Desai - Marketing Manager
        "assigned_teams": [3],  # Digital Marketing Team
        "start_date": datetime.now() - timedelta(days=5),
        "end_date": datetime.now() + timedelta(days=90),
        "status": "active"
    },
    
    # HUMAN RESOURCES PROJECTS
    {
        "name": "Remote Work Policy Implementation",
        "description": "Develop and implement comprehensive remote work policies and procedures",
        "manager_id": 17,  # Vijay Menon - HR Manager
        "assigned_teams": [4],  # HR Operations Team
        "start_date": datetime.now() - timedelta(days=40),
        "end_date": datetime.now() + timedelta(days=20),
        "status": "active"
    },
    {
        "name": "Employee Training Program",
        "description": "Create comprehensive training program for new hires and skill development",
        "manager_id": 17,  # Vijay Menon - HR Manager
        "assigned_teams": [4],  # HR Operations Team
        "start_date": datetime.now() - timedelta(days=15),
        "end_date": datetime.now() + timedelta(days=45),
        "status": "active"
    },
    
    # FINANCE PROJECTS
    {
        "name": "Budget Planning 2024",
        "description": "Develop comprehensive budget plan for fiscal year 2024 with department allocations",
        "manager_id": 21,  # Srinivas Rao - Finance Manager
        "assigned_teams": [5],  # Finance Operations Team
        "start_date": datetime.now() - timedelta(days=50),
        "end_date": datetime.now() + timedelta(days=10),
        "status": "active"
    },
    {
        "name": "Financial Compliance Audit",
        "description": "Conduct annual financial compliance audit and prepare regulatory reports",
        "manager_id": 21,  # Srinivas Rao - Finance Manager
        "assigned_teams": [5],  # Finance Operations Team
        "start_date": datetime.now() - timedelta(days=35),
        "end_date": datetime.now() + timedelta(days=15),
        "status": "active"
    },
    
    # OPERATIONS PROJECTS
    {
        "name": "Process Standardization Initiative",
        "description": "Standardize and document all operational processes across departments",
        "manager_id": 25,  # Ramesh Kumar - Operations Manager
        "assigned_teams": [6],  # Operations Excellence Team
        "start_date": datetime.now() - timedelta(days=70),
        "end_date": datetime.now() + timedelta(days=50),
        "status": "active"
    },
    {
        "name": "Quality Management System",
        "description": "Implement ISO 9001 quality management system across all operations",
        "manager_id": 25,  # Ramesh Kumar - Operations Manager
        "assigned_teams": [6],  # Operations Excellence Team
        "start_date": datetime.now() - timedelta(days=20),
        "end_date": datetime.now() + timedelta(days=100),
        "status": "active"
    },
    
    # IT PROJECTS
    {
        "name": "Cloud Infrastructure Migration",
        "description": "Migrate on-premises infrastructure to cloud-based solutions for better scalability",
        "manager_id": 29,  # Rajiv Mehta - IT Manager
        "assigned_teams": [7],  # IT Operations Team
        "start_date": datetime.now() - timedelta(days=80),
        "end_date": datetime.now() + timedelta(days=60),
        "status": "active"
    },
    {
        "name": "Cybersecurity Enhancement",
        "description": "Implement advanced cybersecurity measures and employee training program",
        "manager_id": 29,  # Rajiv Mehta - IT Manager
        "assigned_teams": [7],  # IT Operations Team
        "start_date": datetime.now() - timedelta(days=30),
        "end_date": datetime.now() + timedelta(days=90),
        "status": "active"
    },
    
    # SALES PROJECTS
    {
        "name": "CRM System Integration",
        "description": "Integrate new CRM system with existing sales processes and customer data",
        "manager_id": 12,  # Meera Joshi - Sales Manager
        "assigned_teams": [8, 9],  # Enterprise Sales Team, SMB Sales Team
        "start_date": datetime.now() - timedelta(days=25),
        "end_date": datetime.now() + timedelta(days=35),
        "status": "active"
    },
    {
        "name": "Sales Training Program",
        "description": "Develop and implement comprehensive sales training program for all sales staff",
        "manager_id": 12,  # Meera Joshi - Sales Manager
        "assigned_teams": [8, 9],  # Enterprise Sales Team, SMB Sales Team
        "start_date": datetime.now() - timedelta(days=10),
        "end_date": datetime.now() + timedelta(days=30),
        "status": "active"
    },
    
    # COMPLETED PROJECTS
    {
        "name": "Website Redesign Phase 1",
        "description": "Completed initial phase of website redesign with new homepage and navigation",
        "manager_id": 8,  # Anita Desai - Marketing Manager
        "assigned_teams": [1, 3],  # Frontend Team, Digital Marketing
        "start_date": datetime.now() - timedelta(days=120),
        "end_date": datetime.now() - timedelta(days=30),
        "status": "completed"
    },
    {
        "name": "Employee Handbook Update",
        "description": "Updated and distributed new employee handbook with current policies",
        "manager_id": 17,  # Vijay Menon - HR Manager
        "assigned_teams": [4],  # HR Operations Team
        "start_date": datetime.now() - timedelta(days=90),
        "end_date": datetime.now() - timedelta(days=60),
        "status": "completed"
    }
]

def get_demo_projects():
    """Return list of ProjectCreate objects for demo projects"""
    return [ProjectCreate(**project_data) for project_data in DEMO_PROJECTS]

def get_projects_by_status():
    """Return projects grouped by status"""
    status_groups = {}
    for project_data in DEMO_PROJECTS:
        status = project_data["status"]
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(project_data)
    return status_groups

def get_projects_by_manager():
    """Return projects grouped by manager"""
    manager_groups = {}
    for project_data in DEMO_PROJECTS:
        manager_id = project_data["manager_id"]
        if manager_id not in manager_groups:
            manager_groups[manager_id] = []
        manager_groups[manager_id].append(project_data)
    return manager_groups

def get_cross_department_projects():
    """Return projects that involve multiple departments"""
    cross_dept = []
    for project_data in DEMO_PROJECTS:
        # Projects with more than 2 teams are likely cross-department
        if len(project_data["assigned_teams"]) >= 3:
            cross_dept.append(project_data)
    return cross_dept

if __name__ == "__main__":
    print("Demo Projects Data")
    print("==================")
    print(f"Total Projects: {len(DEMO_PROJECTS)}")
    
    print("\nBy Status:")
    status_projects = get_projects_by_status()
    for status, projects in status_projects.items():
        print(f"  {status.title()}: {len(projects)} projects")
    
    print("\nCross-Department Projects:")
    cross_dept = get_cross_department_projects()
    for project in cross_dept:
        print(f"  - {project['name']} ({len(project['assigned_teams'])} teams)")
    
    print("\nProject Timeline:")
    for project in DEMO_PROJECTS:
        duration = (project['end_date'] - project['start_date']).days
        print(f"  {project['name']}: {duration} days ({project['status']})")
