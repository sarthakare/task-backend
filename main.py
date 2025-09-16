from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.routers import auth, user, team, project, task, dashboard, reminder
from app.utils.auth import get_current_user
from app.models.user import User
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

app = FastAPI()

# WebSocket connection management with user tracking
class ConnectionInfo:
    def __init__(self, websocket: WebSocket, user_id: int, user_name: str, user_role: str, user_department: str, team_ids: List[int] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.user_name = user_name
        self.user_role = user_role
        self.user_department = user_department
        self.team_ids = team_ids or []
        self.connected_at = datetime.now()

# Store connections with user information
active_connections: Dict[int, ConnectionInfo] = {}  # user_id -> ConnectionInfo

# Message targeting types
class MessageTarget(Enum):
    ALL = "all"
    USER = "user"
    TEAM = "team"
    DEPARTMENT = "department"
    ROLE = "role"

# Helper function to send message to specific connections
async def send_to_connections(connections: List[ConnectionInfo], message: str):
    """Send a message to specific connections"""
    if not connections:
        return
    
    tasks = []
    for connection in connections:
        try:
            tasks.append(connection.websocket.send_text(message))
        except Exception as e:
            print(f"Error sending message to user {connection.user_id}: {e}")
            # Remove the broken connection
            if connection.user_id in active_connections:
                del active_connections[connection.user_id]
    
    # Send to all connections concurrently
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

# Helper function to broadcast messages to all connected clients
async def broadcast_message(message: str):
    """Send a message to all connected WebSocket clients"""
    connections = list(active_connections.values())
    await send_to_connections(connections, message)

# Helper function to send message to specific user
async def send_to_user(user_id: int, message: str):
    """Send a message to a specific user"""
    print(f"send_to_user called with user_id: {user_id}")
    print(f"Available connections: {list(active_connections.keys())}")
    
    if user_id in active_connections:
        print(f"Found connection for user {user_id}, sending message")
        await send_to_connections([active_connections[user_id]], message)
    else:
        print(f"No active connection found for user {user_id}")

# Helper function to send message to users by team
async def send_to_team(team_id: int, message: str):
    """Send a message to all users in a specific team"""
    team_connections = [
        conn for conn in active_connections.values() 
        if team_id in conn.team_ids
    ]
    await send_to_connections(team_connections, message)

# Helper function to send message to users by department
async def send_to_department(department: str, message: str):
    """Send a message to all users in a specific department"""
    dept_connections = [
        conn for conn in active_connections.values() 
        if conn.user_department == department
    ]
    await send_to_connections(dept_connections, message)

# Helper function to send message to users by role
async def send_to_role(role: str, message: str):
    """Send a message to all users with a specific role"""
    role_connections = [
        conn for conn in active_connections.values() 
        if conn.user_role == role
    ]
    await send_to_connections(role_connections, message)

# Enhanced toast notification function with targeting
async def send_toast(
    toast_type: str, 
    title: str, 
    message: str, 
    target: MessageTarget = MessageTarget.ALL,
    target_id: Optional[str] = None,
    data: dict = None
):
    """Send a structured toast notification with targeting support"""
    toast_data = {
        "type": "toast",
        "toast_type": toast_type,  # "success", "error", "warning", "info"
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "target": target.value,
        "target_id": target_id,
        "data": data or {}
    }
    
    json_message = json.dumps(toast_data)
    
    # Send based on target type
    if target == MessageTarget.ALL:
        await broadcast_message(json_message)
    elif target == MessageTarget.USER and target_id:
        await send_to_user(int(target_id), json_message)
    elif target == MessageTarget.TEAM and target_id:
        await send_to_team(int(target_id), json_message)
    elif target == MessageTarget.DEPARTMENT and target_id:
        await send_to_department(target_id, json_message)
    elif target == MessageTarget.ROLE and target_id:
        await send_to_role(target_id, json_message)

# Legacy function for backward compatibility
async def broadcast_toast(toast_type: str, title: str, message: str, data: dict = None):
    """Send a structured toast notification to all connected WebSocket clients"""
    await send_toast(toast_type, title, message, MessageTarget.ALL, None, data)

# CORS configuration
origins = [
    "https://task-frontend-neon.vercel.app",  # Production frontend - vercel
    "https://task-frontend-production-b4dc.up.railway.app",  # Production frontend - railway
    "http://localhost:3000",                  # Local development frontend
    "http://localhost:3001",                  # Local development frontend
    "http://localhost:3002",                  # Local development frontend
    "http://127.0.0.1:3000",                 # Alternative localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(team.router, prefix="/teams", tags=["Teams"])
app.include_router(project.router, prefix="/projects", tags=["Projects"])
app.include_router(task.router, tags=["Tasks"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(reminder.router, tags=["Reminders"])

# Root route
@app.get("/")
def read_root():
    return {"message": "Task Manager API"}

@app.get("/health")
def health():
  return {"status": "ok"}

# WebSocket endpoint for real-time communication with authentication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket.accept()
    
    # Default values for demo/fallback
    user_id = None
    user_name = "Anonymous"
    user_role = "user"
    user_department = "General"
    team_ids = []
    
    # Try to authenticate if token is provided
    if token:
        try:
            # Import here to avoid circular imports
            from app.utils.auth import verify_token
            from app.database import get_db
            from app.models.user import User
            from sqlalchemy.orm import Session
            
            # Verify the JWT token
            payload = verify_token(token)
            if payload and "sub" in payload:
                # Get user from database using email (JWT sub contains email)
                db = next(get_db())
                user = db.query(User).filter(User.email == payload["sub"]).first()
                if user and user.is_active:
                    user_id = user.id
                    user_name = user.name
                    user_role = user.role
                    user_department = user.department
                    
                    # Get user's team IDs
                    team_ids = [team.id for team in user.teams] if hasattr(user, 'teams') else []
                    
                    print(f"WebSocket authenticated user: {user_name} (ID: {user_id})")
                else:
                    print(f"User not found or inactive: {payload.get('sub')}")
            else:
                print("Invalid token payload")
        except Exception as e:
            print(f"WebSocket authentication failed: {e}")
            # Continue with anonymous connection for demo purposes
    else:
        print("No token provided, using anonymous connection")
    
    # Create connection info
    connection_info = ConnectionInfo(
        websocket=websocket,
        user_id=user_id or len(active_connections) + 1,  # Demo user ID if no auth
        user_name=user_name,
        user_role=user_role,
        user_department=user_department,
        team_ids=team_ids
    )
    
    # Add to active connections
    active_connections[connection_info.user_id] = connection_info
    
    # Send welcome message to the new connection
    welcome_data = {
        "type": "message",
        "content": f"Welcome {user_name}! Connected to WebSocket server",
        "timestamp": datetime.now().isoformat(),
        "user_info": {
            "user_id": connection_info.user_id,
            "user_name": user_name,
            "user_role": user_role,
            "user_department": user_department
        }
    }
    await websocket.send_text(json.dumps(welcome_data))
    
    # Broadcast toast notification to all users that someone joined
    await send_toast(
        toast_type="info",
        title="User Connected",
        message=f"{user_name} has joined the chat. Total users: {len(active_connections)}",
        target=MessageTarget.ALL,
        data={"connection_count": len(active_connections), "new_user": user_name}
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Try to parse as JSON, if it fails, treat as plain text
            try:
                received_data = json.loads(data)
                
                # Handle different message types
                if received_data.get("type") == "message":
                    # Regular message - determine target
                    target = MessageTarget(received_data.get("target", "all"))
                    target_id = received_data.get("target_id")
                    content = received_data.get("content", data)
                    
                    # Send based on target
                    if target == MessageTarget.ALL:
                        await send_toast(
                            toast_type="success",
                            title=f"Message from {user_name}",
                            message=content,
                            target=MessageTarget.ALL,
                            data={"original_message": received_data, "sender": user_name}
                        )
                    elif target == MessageTarget.USER and target_id:
                        await send_toast(
                            toast_type="info",
                            title=f"Direct message from {user_name}",
                            message=content,
                            target=MessageTarget.USER,
                            target_id=target_id,
                            data={"original_message": received_data, "sender": user_name}
                        )
                    elif target == MessageTarget.TEAM and target_id:
                        await send_toast(
                            toast_type="info",
                            title=f"Team message from {user_name}",
                            message=content,
                            target=MessageTarget.TEAM,
                            target_id=target_id,
                            data={"original_message": received_data, "sender": user_name}
                        )
                    elif target == MessageTarget.DEPARTMENT and target_id:
                        await send_toast(
                            toast_type="info",
                            title=f"Department message from {user_name}",
                            message=content,
                            target=MessageTarget.DEPARTMENT,
                            target_id=target_id,
                            data={"original_message": received_data, "sender": user_name}
                        )
                    elif target == MessageTarget.ROLE and target_id:
                        await send_toast(
                            toast_type="info",
                            title=f"Role message from {user_name}",
                            message=content,
                            target=MessageTarget.ROLE,
                            target_id=target_id,
                            data={"original_message": received_data, "sender": user_name}
                        )
                        
                elif received_data.get("type") == "demo":
                    # Handle demo toast requests
                    target = MessageTarget(received_data.get("target", "all"))
                    target_id = received_data.get("target_id")
                    
                    await send_toast(
                        toast_type=received_data.get("toast_type", "info"),
                        title=received_data.get("title", "Demo Toast"),
                        message=received_data.get("message", "Demo notification"),
                        target=target,
                        target_id=target_id,
                        data={"demo_data": received_data, "sender": user_name}
                    )
                    
                elif received_data.get("type") == "get_users":
                    # Send list of connected users
                    users_list = [
                        {
                            "user_id": conn.user_id,
                            "user_name": conn.user_name,
                            "user_role": conn.user_role,
                            "user_department": conn.user_department,
                            "connected_at": conn.connected_at.isoformat()
                        }
                        for conn in active_connections.values()
                    ]
                    
                    response_data = {
                        "type": "users_list",
                        "users": users_list,
                        "total_count": len(users_list),
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response_data))
                    
                else:
                    # Forward structured data as toast
                    await send_toast(
                        toast_type="info",
                        title="Data Received",
                        message=str(received_data),
                        target=MessageTarget.ALL,
                        data=received_data
                    )
                    
            except json.JSONDecodeError:
                # Plain text message - send as broadcast
                await send_toast(
                    toast_type="success",
                    title=f"Message from {user_name}",
                    message=data,
                    target=MessageTarget.ALL,
                    data={"message_type": "text", "sender": user_name}
                )
                
    except WebSocketDisconnect:
        # Remove from active connections
        if connection_info.user_id in active_connections:
            del active_connections[connection_info.user_id]
            
        # Broadcast toast notification to remaining users that someone disconnected
        await send_toast(
            toast_type="warning",
            title="User Disconnected",
            message=f"{user_name} has left the chat. Remaining users: {len(active_connections)}",
            target=MessageTarget.ALL,
            data={"connection_count": len(active_connections), "disconnected_user": user_name}
        )
