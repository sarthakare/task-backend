from fastapi import FastAPI
from app.routers import auth, tasks, user, task_log
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",  # Dev frontend
    "https://task-frontend-sarthak-thakares-projects.vercel.app",  # Uncomment in production
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
app.include_router(task_log.router, prefix="/logs", tags=["Logs"])  # ✅ Corrected

# Root route
@app.get("/")
def read_root():
    return {"message": "Task Manager API"}

@app.get("/health")
def health():
  return {"status": "ok"}
