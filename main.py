from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.routers import auth, tasks, user, task_log, reports, hierarchy, notifications
from app.routers.notifications import router as notifications_router
from fastapi.middleware.cors import CORSMiddleware
from app.services.websocket_manager import websocket_manager
from app.utils.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import user as user_model

app = FastAPI()

# CORS configuration
origins = [
    "https://task-frontend-neon.vercel.app",  # Production frontend
    "http://localhost:3000",                  # Local development frontend
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
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(task_log.router, prefix="/logs", tags=["Logs"]) 
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(hierarchy.router, prefix="/hierarchy", tags=["Hierarchy"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

# Root route
@app.get("/")
def read_root():
    return {"message": "Task Manager API"}

@app.get("/health")
def health():
  return {"status": "ok"}

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Add to WebSocket manager
        await websocket_manager.connect(websocket, user_id)
        
        print(f"🔌 WebSocket connected for user {user_id}")
        
        # Keep connection alive and handle messages
        try:
            while True:
                # Wait for any message from client (ping/pong or other)
                data = await websocket.receive_text()
                print(f"📨 Received message from user {user_id}: {data}")
                
                # You can handle different message types here
                # For now, just echo back or handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                
        except WebSocketDisconnect:
            print(f"🔌 WebSocket disconnected for user {user_id}")
        except Exception as e:
            print(f"❌ WebSocket error for user {user_id}: {e}")
        finally:
            # Clean up connection
            websocket_manager.disconnect(websocket, user_id)
            
    except Exception as e:
        print(f"❌ Error in WebSocket connection: {e}")
        try:
            await websocket.close()
        except:
            pass
