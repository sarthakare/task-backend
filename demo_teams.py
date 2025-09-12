"""
Demo Teams Data for Task Manager Application
Creates teams for each department with appropriate leaders and members
"""

from datetime import datetime
from app.schemas.team import TeamCreate

# Demo Teams Data
# Structure: Team Name, Description, Department, Leader ID, Member IDs
DEMO_TEAMS = [
    # ENGINEERING TEAMS
    {
        "name": "Frontend Development Team",
        "description": "Responsible for user interface and user experience development",
        "department": "Engineering",
        "leader_id": 4,  # Priya Sharma - Frontend Team Lead
        "member_ids": [6],  # Deepika Patel - Frontend Developer
        "status": "active"
    },
    {
        "name": "Backend Development Team",
        "description": "Handles server-side logic, databases, and API development",
        "department": "Engineering",
        "leader_id": 5,  # Arjun Singh - Backend Team Lead
        "member_ids": [7],  # Vikram Reddy - Backend Developer
        "status": "active"
    },
    
    # MARKETING TEAMS
    {
        "name": "Digital Marketing Team",
        "description": "Handles online marketing campaigns, SEO, and digital advertising",
        "department": "Marketing",
        "leader_id": 8,  # Suresh Gupta - Digital Marketing Team Lead
        "member_ids": [9, 10],  # Kavya Nair, Rohit Agarwal - Marketing Members
        "status": "active"
    },
    
    # HUMAN RESOURCES TEAMS
    {
        "name": "HR Operations Team",
        "description": "Handles HR operations, employee relations, and workplace policies",
        "department": "HR",
        "leader_id": 17,  # Shalini Verma - HR Team Lead
        "member_ids": [18, 19],  # Nikhil Jain, Geeta Krishnan - HR Members
        "status": "active"
    },
    
    # FINANCE TEAMS
    {
        "name": "Finance Operations Team",
        "description": "Handles financial operations, accounting, and analysis",
        "department": "Finance",
        "leader_id": 21,  # Rekha Sood - Finance Team Lead
        "member_ids": [22, 23],  # Manish Tiwari, Lakshmi Nair - Finance Members
        "status": "active"
    },
    
    # OPERATIONS TEAMS
    {
        "name": "Operations Excellence Team",
        "description": "Handles process improvement and quality assurance",
        "department": "Operations",
        "leader_id": 25,  # Sarita Malhotra - Operations Team Lead
        "member_ids": [26, 27],  # Kiran Bajaj, Gopal Sharma - Operations Members
        "status": "active"
    },
    
    # IT TEAMS
    {
        "name": "IT Operations Team",
        "description": "Manages IT infrastructure, security, and system administration",
        "department": "IT",
        "leader_id": 29,  # Neha Chopra - IT Team Lead
        "member_ids": [30, 31],  # Sandeep Agarwal, Divya Singh - IT Members
        "status": "active"
    },
    
    # SALES TEAMS
    {
        "name": "Enterprise Sales Team",
        "description": "Focuses on large enterprise clients and strategic accounts",
        "department": "Sales",
        "leader_id": 12,  # Amit Khanna - Enterprise Sales Team Lead
        "member_ids": [14],  # Ravi Mishra - Enterprise Sales Representative
        "status": "active"
    },
    {
        "name": "SMB Sales Team",
        "description": "Handles small and medium business clients and leads",
        "department": "Sales",
        "leader_id": 13,  # Sunita Rao - SMB Sales Team Lead
        "member_ids": [15],  # Pooja Iyer - SMB Sales Representative
        "status": "active"
    }
]

def get_demo_teams():
    """Return list of TeamCreate objects for demo teams"""
    return [TeamCreate(**team_data) for team_data in DEMO_TEAMS]

def get_teams_by_department():
    """Return teams grouped by department"""
    departments = {}
    for team_data in DEMO_TEAMS:
        dept = team_data["department"]
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(team_data)
    return departments

def get_team_hierarchy():
    """Return team hierarchy with leaders and members"""
    hierarchy = {}
    for team_data in DEMO_TEAMS:
        team_name = team_data["name"]
        hierarchy[team_name] = {
            "department": team_data["department"],
            "leader_id": team_data["leader_id"],
            "member_ids": team_data["member_ids"],
            "total_members": len(team_data["member_ids"]) + 1  # +1 for leader
        }
    return hierarchy

if __name__ == "__main__":
    print("Demo Teams Data")
    print("===============")
    print(f"Total Teams: {len(DEMO_TEAMS)}")
    print("\nBy Department:")
    dept_teams = get_teams_by_department()
    for dept, teams in dept_teams.items():
        print(f"  {dept}: {len(teams)} teams")
        for team in teams:
            print(f"    - {team['name']} (Leader: {team['leader_id']}, Members: {len(team['member_ids'])})")
    
    print("\nTeam Hierarchy:")
    hierarchy = get_team_hierarchy()
    for team_name, info in hierarchy.items():
        print(f"  {team_name}: {info['total_members']} total members")
