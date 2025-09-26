# app/routers/team.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio
import threading
from app.database import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamOut, TeamMemberAdd
from app.utils.auth import get_current_user
from app.utils.hierarchy import HierarchyManager

router = APIRouter()

# WebSocket notification helper functions
async def send_team_notification(
    notification_type: str,
    title: str,
    message: str,
    target_user_ids: List[int] = None,
    team_data: dict = None
):
    """Send team-related WebSocket notification"""
    try:
        # Import here to avoid circular imports
        from main import send_toast, MessageTarget, send_to_user, broadcast_message, active_connections
        import json
        
        print(f"Sending team notification: {notification_type} to users {target_user_ids}")
        print(f"Active connections: {list(active_connections.keys())}")
        
        notification_data = {
            "type": "team_notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "team_data": team_data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        json_message = json.dumps(notification_data)
        
        if target_user_ids:
            # Send to specific users
            for user_id in target_user_ids:
                print(f"Attempting to send to user {user_id}")
                await send_to_user(user_id, json_message)
        else:
            print("Broadcasting to all users")
            await broadcast_message(json_message)
            
    except Exception as e:
        print(f"Error sending team notification: {e}")
        import traceback
        traceback.print_exc()

def send_team_notification_async(
    notification_type: str,
    title: str,
    message: str,
    target_user_ids: List[int] = None,
    team_data: dict = None
):
    """Helper function to send team notifications asynchronously from sync context"""
    def run_notification():
        try:
            # Ensure team_data is properly serialized
            if team_data:
                serialized_team_data = {}
                for key, value in team_data.items():
                    if hasattr(value, 'value'):  # Handle enums
                        serialized_team_data[key] = value.value
                    elif hasattr(value, 'isoformat'):  # Handle datetime
                        serialized_team_data[key] = value.isoformat()
                    else:
                        serialized_team_data[key] = value
            else:
                serialized_team_data = None
                
            asyncio.run(send_team_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                target_user_ids=target_user_ids,
                team_data=serialized_team_data
            ))
        except Exception as e:
            print(f"Error in team notification thread: {e}")
            import traceback
            traceback.print_exc()
    
    # Run in a separate thread to avoid blocking the main request
    thread = threading.Thread(target=run_notification, daemon=True)
    thread.start()

@router.get("/", response_model=List[TeamOut])
def get_all_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get teams based on user's role and hierarchy scope"""
    
    hierarchy_manager = HierarchyManager(db)
    user_role = current_user.role.upper()
    
    if user_role in ['ADMIN', 'CEO']:
        # Admin and CEO see all teams
        teams = db.query(Team).all()
    else:
        # Other roles see only their relevant teams
        user_teams = []
        
        # Get teams where user is the leader
        teams_leading = db.query(Team).filter(Team.leader_id == current_user.id).all()
        user_teams.extend(teams_leading)
        
        # Get teams where user is a member
        teams_member = db.query(Team).join(Team.members).filter(
            Team.members.any(User.id == current_user.id)
        ).all()
        user_teams.extend(teams_member)
        
        # For managers, also include teams of their subordinates
        if user_role == 'MANAGER':
            subordinates = hierarchy_manager.get_all_subordinates(current_user.id)
            for subordinate in subordinates:
                # Teams led by subordinates
                subordinate_teams = db.query(Team).filter(Team.leader_id == subordinate.id).all()
                user_teams.extend(subordinate_teams)
                
                # Teams where subordinates are members
                subordinate_member_teams = db.query(Team).join(Team.members).filter(
                    Team.members.any(User.id == subordinate.id)
                ).all()
                user_teams.extend(subordinate_member_teams)
        
        # Remove duplicates and return
        unique_teams = list(set([team.id for team in user_teams]))
        if unique_teams:
            teams = db.query(Team).filter(Team.id.in_(unique_teams)).all()
        else:
            teams = []
    
    return teams

@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(team_data: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new team - Only admin and CEO can create teams"""
    
    # Check if user has permission to create teams
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can create teams"
        )
    
    # Check if team name already exists
    existing_team = db.query(Team).filter(Team.name == team_data.name).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    # Check if leader exists and is active
    leader = db.query(User).filter(User.id == team_data.leader_id).first()
    if not leader:
        raise HTTPException(status_code=400, detail="Team leader not found")
    if not leader.is_active:
        raise HTTPException(status_code=400, detail="Team leader is not active")
    
    # Check if all members exist and are active
    members = []
    if team_data.member_ids:
        members = db.query(User).filter(User.id.in_(team_data.member_ids)).all()
        if len(members) != len(team_data.member_ids):
            raise HTTPException(status_code=400, detail="One or more team members not found")
        
        inactive_members = [member.name for member in members if not member.is_active]
        if inactive_members:
            raise HTTPException(
                status_code=400, 
                detail=f"The following team members are inactive: {', '.join(inactive_members)}"
            )
    
    # Ensure leader is included in members
    if team_data.leader_id not in team_data.member_ids:
        team_data.member_ids.append(team_data.leader_id)
        members.append(leader)
    
    # Create new team
    db_team = Team(
        name=team_data.name,
        description=team_data.description,
        department=team_data.department,
        leader_id=team_data.leader_id,
        status=team_data.status or "active"
    )
    
    # Add team to database
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # Add members to team
    db_team.members = members
    db.commit()
    db.refresh(db_team)
    
    # Send WebSocket notification to all team members
    try:
        # Create team data for notification
        team_data = {
            "team_id": db_team.id,
            "team_name": db_team.name,
            "description": db_team.description,
            "department": db_team.department,
            "status": db_team.status,
            "leader_name": leader.name,
            "member_count": len(members),
            "created_by": current_user.name
        }
        
        # Get all team member IDs
        team_member_ids = [member.id for member in members]
        
        # Send notification to all team members
        send_team_notification_async(
            notification_type="team_created",
            title="New Team Created",
            message=f"You have been added to the new team '{db_team.name}' by {current_user.name}",
            target_user_ids=team_member_ids,
            team_data=team_data
        )
        
    except Exception as e:
        print(f"Error sending team creation notification: {e}")
        # Don't fail the main operation if notification fails
    
    return db_team

@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a team - Only admin and CEO can edit teams"""
    
    # Check if user has permission to edit teams
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can edit teams"
        )
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if team name already exists for another team
    if team_update.name and team_update.name != db_team.name:
        existing_team = db.query(Team).filter(
            Team.name == team_update.name,
            Team.id != team_id
        ).first()
        if existing_team:
            raise HTTPException(status_code=400, detail="Team name already exists")
    
    # Check if new leader exists and is active
    if team_update.leader_id and team_update.leader_id != db_team.leader_id:
        leader = db.query(User).filter(User.id == team_update.leader_id).first()
        if not leader:
            raise HTTPException(status_code=400, detail="Team leader not found")
        if not leader.is_active:
            raise HTTPException(status_code=400, detail="Team leader is not active")
    
    # Handle member updates
    if team_update.member_ids is not None:
        # Check if all members exist and are active
        members = db.query(User).filter(User.id.in_(team_update.member_ids)).all()
        if len(members) != len(team_update.member_ids):
            raise HTTPException(status_code=400, detail="One or more team members not found")
        
        inactive_members = [member.name for member in members if not member.is_active]
        if inactive_members:
            raise HTTPException(
                status_code=400, 
                detail=f"The following team members are inactive: {', '.join(inactive_members)}"
            )
        
        # Ensure leader is included in members
        leader_id = team_update.leader_id or db_team.leader_id
        if leader_id not in team_update.member_ids:
            team_update.member_ids.append(leader_id)
            leader = db.query(User).filter(User.id == leader_id).first()
            members.append(leader)
        
        # Update members
        db_team.members = members
    
    # Update team fields
    update_data = team_update.model_dump(exclude_unset=True, exclude={'member_ids'})
    for field, value in update_data.items():
        setattr(db_team, field, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a team - Only admin and CEO can delete teams"""
    
    # Check if user has permission to delete teams
    if current_user.role.upper() not in ["ADMIN", "CEO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and CEO users can delete teams"
        )
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Remove all members from team before deleting
    db_team.members.clear()
    db.delete(db_team)
    db.commit()
    return None

@router.get("/{team_id}/members", response_model=List[dict])
def get_team_members(team_id: int, db: Session = Depends(get_db)):
    """Get all members of a specific team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return [
        {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "role": member.role,
            "department": member.department,
            "is_leader": member.id == team.leader_id
        }
        for member in team.members
    ]

@router.post("/{team_id}/members", response_model=dict)
def add_team_member(team_id: int, member_data: TeamMemberAdd, db: Session = Depends(get_db)):
    """Add a member to a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    
    # Check if user is already a member
    if user in team.members:
        raise HTTPException(status_code=400, detail="User is already a team member")
    
    team.members.append(user)
    db.commit()
    
    return {"message": f"User {user.name} added to team {team.name}"}

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(team_id: int, user_id: int, db: Session = Depends(get_db)):
    """Remove a member from a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is a member
    if user not in team.members:
        raise HTTPException(status_code=400, detail="User is not a team member")
    
    # Prevent removing team leader
    if user.id == team.leader_id:
        raise HTTPException(status_code=400, detail="Cannot remove team leader. Change leader first.")
    
    team.members.remove(user)
    db.commit()
    return None

@router.get("/stats/")
def get_team_stats(db: Session = Depends(get_db)):
    """Get team statistics"""
    total_teams = db.query(Team).count()
    active_teams = db.query(Team).filter(Team.status == "active").count()
    inactive_teams = db.query(Team).filter(Team.status == "inactive").count()
    
    # Count by department
    department_counts = {}
    departments = ['engineering', 'marketing', 'sales', 'hr', 'finance', 'operations', 'it']
    for dept in departments:
        count = db.query(Team).filter(Team.department == dept).count()
        department_counts[dept] = count
    
    return {
        "total_teams": total_teams,
        "active_teams": active_teams,
        "inactive_teams": inactive_teams,
        "department_counts": department_counts
    }
