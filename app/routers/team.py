# app/routers/team.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamOut, TeamMemberAdd
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[TeamOut])
def get_all_teams(db: Session = Depends(get_db)):
    """Get all teams with their leaders and members"""
    teams = db.query(Team).all()
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
