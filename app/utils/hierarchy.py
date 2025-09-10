# app/utils/hierarchy.py
from typing import List, Set
from sqlalchemy.orm import Session
from app.models.user import User


class HierarchyManager:
    """Utility class for managing organizational hierarchy operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_subordinates(self, user_id: int) -> List[User]:
        """Get all subordinates (direct and indirect) for a given user"""
        subordinates = []
        visited = set()
        
        def collect_subordinates(supervisor_id: int):
            if supervisor_id in visited:
                return
            visited.add(supervisor_id)
            
            # Get direct subordinates (both active and inactive)
            direct_subordinates = self.db.query(User).filter(
                User.supervisor_id == supervisor_id
            ).all()
            
            for subordinate in direct_subordinates:
                subordinates.append(subordinate)
                # Recursively get their subordinates
                collect_subordinates(subordinate.id)
        
        collect_subordinates(user_id)
        return subordinates
    
    def get_direct_subordinates(self, user_id: int) -> List[User]:
        """Get only direct subordinates for a given user"""
        return self.db.query(User).filter(
            User.supervisor_id == user_id
        ).all()
    
    def get_supervisory_chain(self, user_id: int) -> List[User]:
        """Get the complete supervisory chain from user to top level"""
        chain = []
        current_user = self.db.query(User).filter(User.id == user_id).first()
        
        while current_user and current_user.supervisor_id:
            supervisor = self.db.query(User).filter(
                User.id == current_user.supervisor_id
            ).first()
            if supervisor:
                chain.append(supervisor)
                current_user = supervisor
            else:
                break
        
        return chain
    
    def is_subordinate_of(self, user_id: int, potential_supervisor_id: int) -> bool:
        """Check if user_id is a subordinate (direct or indirect) of potential_supervisor_id"""
        supervisory_chain = self.get_supervisory_chain(user_id)
        return any(supervisor.id == potential_supervisor_id for supervisor in supervisory_chain)
    
    def is_peer_or_subordinate(self, user_id: int, target_user_id: int) -> bool:
        """Check if target_user can be assigned tasks by user_id (peer or subordinate)"""
        if user_id == target_user_id:
            return True
        
        user = self.db.query(User).filter(User.id == user_id).first()
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        
        if not user or not target_user:
            return False
        
        # Check if they are peers (same supervisor)
        if user.supervisor_id == target_user.supervisor_id and user.supervisor_id is not None:
            return True
        
        # Check if target is a subordinate
        return self.is_subordinate_of(target_user_id, user_id)
    
    def can_view_task(self, user_id: int, task_creator_id: int, task_assignee_id: int) -> bool:
        """Check if user can view a specific task based on hierarchy"""
        # User can view their own tasks (created or assigned)
        if user_id in [task_creator_id, task_assignee_id]:
            return True
        
        # User can view tasks of their subordinates
        if (self.is_subordinate_of(task_creator_id, user_id) or 
            self.is_subordinate_of(task_assignee_id, user_id)):
            return True
        
        return False
    
    def can_modify_task(self, user_id: int, task_creator_id: int, task_assignee_id: int) -> bool:
        """Check if user can modify/reassign a specific task based on role-based scope"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        role = user.role.upper()
        
        # ADMIN and CEO can modify all tasks
        if role in ['ADMIN', 'CEO']:
            return True
        
        # User can modify their own created tasks
        if user_id == task_creator_id:
            return True
        
        # Check if user can modify based on role-based scope
        viewable_user_ids = self.get_viewable_user_ids_by_role(user_id)
        
        # User can modify if the CREATOR is in their scope (hierarchical management)
        # Being an assignee does NOT give modification rights
        if task_creator_id in viewable_user_ids:
            return True
        
        return False
    
    def can_update_task_status(self, user_id: int, task_creator_id: int, task_assignee_id: int) -> bool:
        """Check if user can update task status (more permissive than full modification)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        role = user.role.upper()
        
        # ADMIN and CEO can update status of all tasks
        if role in ['ADMIN', 'CEO']:
            return True
        
        # User can update status of their own created tasks
        if user_id == task_creator_id:
            return True
        
        # User can update status if they are assigned to the task
        if user_id == task_assignee_id:
            return True
        
        # Check if user can update status based on role-based scope
        viewable_user_ids = self.get_viewable_user_ids_by_role(user_id)
        
        # User can update status if the CREATOR is in their scope
        if task_creator_id in viewable_user_ids:
            return True
        
        return False
    
    def get_assignable_users(self, user_id: int) -> List[User]:
        """Get list of users that can be assigned tasks by the given user"""
        assignable_users = []
        
        # Get all subordinates
        subordinates = self.get_all_subordinates(user_id)
        assignable_users.extend(subordinates)
        
        # Get peers (users with same supervisor)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.supervisor_id:
            peers = self.db.query(User).filter(
                User.supervisor_id == user.supervisor_id,
                User.id != user_id,
                User.is_active == True
            ).all()
            assignable_users.extend(peers)
        
        # Add self
        if user:
            assignable_users.append(user)
        
        return assignable_users
    
    def get_user_level(self, user_id: int) -> int:
        """Get the hierarchical level of a user (0 = top level)"""
        level = 0
        current_user = self.db.query(User).filter(User.id == user_id).first()
        
        while current_user and current_user.supervisor_id:
            level += 1
            current_user = self.db.query(User).filter(
                User.id == current_user.supervisor_id
            ).first()
            
            # Prevent infinite loops
            if level > 20:  # Reasonable max depth
                break
        
        return level
    
    def get_team_hierarchy(self, user_id: int) -> dict:
        """Get a hierarchical view of the user's team structure"""
        def build_tree(supervisor_id: int) -> dict:
            subordinates = self.get_direct_subordinates(supervisor_id)
            return {
                "user_id": supervisor_id,
                "subordinates": [build_tree(sub.id) for sub in subordinates]
            }
        
        return build_tree(user_id)
    
    def get_viewable_user_ids_by_role(self, user_id: int) -> List[int]:
        """Get list of user IDs that the current user can view tasks for based on role"""
        from app.models.team import Team, team_members
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        role = user.role.upper()
        viewable_ids = [user_id]  # User can always see their own tasks
        
        if role in ['ADMIN', 'CEO']:
            # ADMIN and CEO can see all tasks
            all_users = self.db.query(User).filter(User.is_active == True).all()
            return [u.id for u in all_users]
        
        elif role == 'MANAGER':
            # Manager can see: own + team_lead + member tasks
            # Get all subordinates through hierarchy
            subordinates = self.get_all_subordinates(user_id)
            for sub in subordinates:
                if sub.role.upper() in ['TEAM_LEAD', 'MEMBER']:
                    viewable_ids.append(sub.id)
            
            # Also include team leads and members from teams they might be managing
            teams_leading = self.db.query(Team).filter(Team.leader_id == user_id).all()
            for team in teams_leading:
                for member in team.members:
                    if member.role.upper() in ['TEAM_LEAD', 'MEMBER'] and member.id not in viewable_ids:
                        viewable_ids.append(member.id)
        
        elif role == 'TEAM_LEAD':
            # Team lead can see: own + member tasks
            # Get all subordinates through hierarchy
            subordinates = self.get_all_subordinates(user_id)
            for sub in subordinates:
                if sub.role.upper() == 'MEMBER':
                    viewable_ids.append(sub.id)
            
            # Also include members from teams they are leading
            teams_leading = self.db.query(Team).filter(Team.leader_id == user_id).all()
            for team in teams_leading:
                for member in team.members:
                    if member.role.upper() == 'MEMBER' and member.id not in viewable_ids:
                        viewable_ids.append(member.id)
        
        elif role == 'MEMBER':
            # Member can only see their own tasks
            pass  # Already included user_id above
        
        return list(set(viewable_ids))  # Remove duplicates
    
    def can_view_task_by_role(self, user_id: int, task_creator_id: int, task_assignee_id: int) -> bool:
        """Check if user can view a specific task based on role-based scope"""
        viewable_ids = self.get_viewable_user_ids_by_role(user_id)
        return task_creator_id in viewable_ids or task_assignee_id in viewable_ids
    
    def get_access_scope_info(self, user_id: int) -> dict:
        """Get information about what the user can access based on their role"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        role = user.role.upper()
        viewable_user_ids = self.get_viewable_user_ids_by_role(user_id)
        viewable_users = self.db.query(User).filter(User.id.in_(viewable_user_ids)).all()
        
        scope_description = {
            'ADMIN': 'Can view all tasks in the system',
            'CEO': 'Can view all tasks in the system', 
            'MANAGER': 'Can view own tasks + team lead tasks + member tasks',
            'TEAM_LEAD': 'Can view own tasks + member tasks',
            'MEMBER': 'Can view only own tasks'
        }
        
        return {
            "user_role": role,
            "scope_description": scope_description.get(role, "Unknown role"),
            "viewable_user_count": len(viewable_users),
            "viewable_users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "role": u.role,
                    "department": u.department
                } for u in viewable_users
            ]
        }