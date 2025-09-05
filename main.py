from fastapi import FastAPI
from app.routers import auth, user, team
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(team.router, prefix="/teams", tags=["Teams"])

# Root route
@app.get("/")
def read_root():
    return {"message": "Task Manager API"}

@app.get("/health")
def health():
  return {"status": "ok"}
