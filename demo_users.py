"""
Demo Users Data for Task Manager Application - Indian Context
Creates users across specified departments with Manager, Team Lead, and Member roles
"""

from datetime import datetime
from app.schemas.user import UserCreate

# Demo Users Data - Indian Context
# Structure: Department -> Role -> Users
DEMO_USERS = [
    # CEO - First position for easy hierarchy management
    {
        "name": "CEO",
        "email": "ceo@test.com",
        "mobile": "+91-98765-43200",
        "password": "password123",
        "department": "All",
        "role": "CEO",
        "supervisor_id": None
    },
    
    # ENGINEERING DEPARTMENT
    {
        "name": "Rajesh Kumar",
        "email": "rajesh.kumar@company.com",
        "mobile": "+91-98765-43210",
        "password": "password123",
        "department": "Engineering",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@company.com",
        "mobile": "+91-98765-43211",
        "password": "password123",
        "department": "Engineering",
        "role": "team_lead",
        "supervisor_id": 3  # Rajesh Kumar - Engineering Manager
    },
    {
        "name": "Arjun Singh",
        "email": "arjun.singh@company.com",
        "mobile": "+91-98765-43212",
        "password": "password123",
        "department": "Engineering",
        "role": "team_lead",
        "supervisor_id": 3  # Rajesh Kumar - Engineering Manager
    },
    {
        "name": "Deepika Patel",
        "email": "deepika.patel@company.com",
        "mobile": "+91-98765-43213",
        "password": "password123",
        "department": "Engineering",
        "role": "member",
        "supervisor_id": 4  # Priya Sharma - Team Lead
    },
    {
        "name": "Vikram Reddy",
        "email": "vikram.reddy@company.com",
        "mobile": "+91-98765-43214",
        "password": "password123",
        "department": "Engineering",
        "role": "member",
        "supervisor_id": 5  # Arjun Singh - Team Lead
    },
    
    # MARKETING DEPARTMENT
    {
        "name": "Anita Desai",
        "email": "anita.desai@company.com",
        "mobile": "+91-98765-43215",
        "password": "password123",
        "department": "Marketing",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Suresh Gupta",
        "email": "suresh.gupta@company.com",
        "mobile": "+91-98765-43216",
        "password": "password123",
        "department": "Marketing",
        "role": "team_lead",
        "supervisor_id": 7  # Anita Desai - Marketing Manager
    },
    {
        "name": "Kavya Nair",
        "email": "kavya.nair@company.com",
        "mobile": "+91-98765-43217",
        "password": "password123",
        "department": "Marketing",
        "role": "member",
        "supervisor_id": 8  # Suresh Gupta - Team Lead
    },
    {
        "name": "Rohit Agarwal",
        "email": "rohit.agarwal@company.com",
        "mobile": "+91-98765-43218",
        "password": "password123",
        "department": "Marketing",
        "role": "member",
        "supervisor_id": 8  # Suresh Gupta - Team Lead
    },
    
    # SALES DEPARTMENT
    {
        "name": "Meera Joshi",
        "email": "meera.joshi@company.com",
        "mobile": "+91-98765-43219",
        "password": "password123",
        "department": "Sales",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Amit Khanna",
        "email": "amit.khanna@company.com",
        "mobile": "+91-98765-43220",
        "password": "password123",
        "department": "Sales",
        "role": "team_lead",
        "supervisor_id": 11  # Meera Joshi - Sales Manager
    },
    {
        "name": "Sunita Rao",
        "email": "sunita.rao@company.com",
        "mobile": "+91-98765-43221",
        "password": "password123",
        "department": "Sales",
        "role": "team_lead",
        "supervisor_id": 11  # Meera Joshi - Sales Manager
    },
    {
        "name": "Ravi Mishra",
        "email": "ravi.mishra@company.com",
        "mobile": "+91-98765-43222",
        "password": "password123",
        "department": "Sales",
        "role": "member",
        "supervisor_id": 12  # Amit Khanna - Team Lead
    },
    {
        "name": "Pooja Iyer",
        "email": "pooja.iyer@company.com",
        "mobile": "+91-98765-43223",
        "password": "password123",
        "department": "Sales",
        "role": "member",
        "supervisor_id": 13  # Sunita Rao - Team Lead
    },
    
    # HUMAN RESOURCES DEPARTMENT
    {
        "name": "Vijay Menon",
        "email": "vijay.menon@company.com",
        "mobile": "+91-98765-43224",
        "password": "password123",
        "department": "HR",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Shalini Verma",
        "email": "shalini.verma@company.com",
        "mobile": "+91-98765-43225",
        "password": "password123",
        "department": "HR",
        "role": "team_lead",
        "supervisor_id": 16  # Vijay Menon - HR Manager
    },
    {
        "name": "Nikhil Jain",
        "email": "nikhil.jain@company.com",
        "mobile": "+91-98765-43226",
        "password": "password123",
        "department": "HR",
        "role": "member",
        "supervisor_id": 17  # Shalini Verma - Team Lead
    },
    {
        "name": "Geeta Krishnan",
        "email": "geeta.krishnan@company.com",
        "mobile": "+91-98765-43227",
        "password": "password123",
        "department": "HR",
        "role": "member",
        "supervisor_id": 17  # Shalini Verma - Team Lead
    },
    
    # FINANCE DEPARTMENT
    {
        "name": "Srinivas Rao",
        "email": "srinivas.rao@company.com",
        "mobile": "+91-98765-43228",
        "password": "password123",
        "department": "Finance",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Rekha Sood",
        "email": "rekha.sood@company.com",
        "mobile": "+91-98765-43229",
        "password": "password123",
        "department": "Finance",
        "role": "team_lead",
        "supervisor_id": 20  # Srinivas Rao - Finance Manager
    },
    {
        "name": "Manish Tiwari",
        "email": "manish.tiwari@company.com",
        "mobile": "+91-98765-43230",
        "password": "password123",
        "department": "Finance",
        "role": "member",
        "supervisor_id": 21  # Rekha Sood - Team Lead
    },
    {
        "name": "Lakshmi Nair",
        "email": "lakshmi.nair@company.com",
        "mobile": "+91-98765-43231",
        "password": "password123",
        "department": "Finance",
        "role": "member",
        "supervisor_id": 21  # Rekha Sood - Team Lead
    },
    
    # OPERATIONS DEPARTMENT
    {
        "name": "Ramesh Kumar",
        "email": "ramesh.kumar@company.com",
        "mobile": "+91-98765-43232",
        "password": "password123",
        "department": "Operations",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Sarita Malhotra",
        "email": "sarita.malhotra@company.com",
        "mobile": "+91-98765-43233",
        "password": "password123",
        "department": "Operations",
        "role": "team_lead",
        "supervisor_id": 24  # Ramesh Kumar - Operations Manager
    },
    {
        "name": "Kiran Bajaj",
        "email": "kiran.bajaj@company.com",
        "mobile": "+91-98765-43234",
        "password": "password123",
        "department": "Operations",
        "role": "member",
        "supervisor_id": 25  # Sarita Malhotra - Team Lead
    },
    {
        "name": "Gopal Sharma",
        "email": "gopal.sharma@company.com",
        "mobile": "+91-98765-43235",
        "password": "password123",
        "department": "Operations",
        "role": "member",
        "supervisor_id": 25  # Sarita Malhotra - Team Lead
    },
    
    # IT DEPARTMENT
    {
        "name": "Rajiv Mehta",
        "email": "rajiv.mehta@company.com",
        "mobile": "+91-98765-43236",
        "password": "password123",
        "department": "IT",
        "role": "manager",
        "supervisor_id": 2  # CEO
    },
    {
        "name": "Neha Chopra",
        "email": "neha.chopra@company.com",
        "mobile": "+91-98765-43237",
        "password": "password123",
        "department": "IT",
        "role": "team_lead",
        "supervisor_id": 28  # Rajiv Mehta - IT Manager
    },
    {
        "name": "Sandeep Agarwal",
        "email": "sandeep.agarwal@company.com",
        "mobile": "+91-98765-43238",
        "password": "password123",
        "department": "IT",
        "role": "member",
        "supervisor_id": 29  # Neha Chopra - Team Lead
    },
    {
        "name": "Divya Singh",
        "email": "divya.singh@company.com",
        "mobile": "+91-98765-43239",
        "password": "password123",
        "department": "IT",
        "role": "member",
        "supervisor_id": 29  # Neha Chopra - Team Lead
    }
]

def get_demo_users():
    """Return list of UserCreate objects for demo users"""
    return [UserCreate(**user_data) for user_data in DEMO_USERS]

def get_users_by_department():
    """Return users grouped by department"""
    departments = {}
    for user_data in DEMO_USERS:
        dept = user_data["department"]
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(user_data)
    return departments

def get_users_by_role():
    """Return users grouped by role"""
    roles = {}
    for user_data in DEMO_USERS:
        role = user_data["role"]
        if role not in roles:
            roles[role] = []
        roles[role].append(user_data)
    return roles

if __name__ == "__main__":
    print("Demo Users Data - Indian Context")
    print("=================================")
    print(f"Total Users: {len(DEMO_USERS)}")
    print("\nBy Department:")
    dept_users = get_users_by_department()
    for dept, users in dept_users.items():
        print(f"  {dept}: {len(users)} users")
    
    print("\nBy Role:")
    role_users = get_users_by_role()
    for role, users in role_users.items():
        print(f"  {role}: {len(users)} users")
    
    print("\nOrganizational Structure:")
    for dept, users in dept_users.items():
        print(f"\n{dept}:")
        managers = [u for u in users if u["role"] == "manager"]
        team_leads = [u for u in users if u["role"] == "team_lead"]
        members = [u for u in users if u["role"] == "member"]
        
        if managers:
            print(f"  Manager: {managers[0]['name']}")
        if team_leads:
            print(f"  Team Leads: {', '.join([tl['name'] for tl in team_leads])}")
        if members:
            print(f"  Members: {', '.join([m['name'] for m in members])}")
