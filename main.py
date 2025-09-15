from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.routers import auth, user, team, project, task, dashboard, reminder
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# WebSocket connection management
active_connections = []

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

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back the received message
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Render.com configuration
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
