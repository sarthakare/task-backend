# app/models/reminder.py
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.database import Base
from datetime import datetime

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)  # Date only, no time component
    priority = Column(String, nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Relationships
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who created the reminder
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who the reminder is assigned to
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Optional task association
    
    # Status
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # System dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_reminders")
    user = relationship("User", foreign_keys=[user_id], back_populates="reminders")
    task = relationship("Task", back_populates="reminders")
