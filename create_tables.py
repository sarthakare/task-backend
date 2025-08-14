from app.database import engine, Base
from app.models import user, tasks, task_log

# Drop all existing tables
Base.metadata.drop_all(bind=engine)
print("✅ All existing tables dropped.")

# Create fresh tables
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully.")
