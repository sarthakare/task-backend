from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, func, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.task_log import TaskLog

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, default="NEW", nullable=False)
    start_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    follow_up_date = Column(DateTime, nullable=True)
    tags = Column(ARRAY(String), default=[])
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")

