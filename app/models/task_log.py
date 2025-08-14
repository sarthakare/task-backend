# app/models/task_log.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    startTime = Column(DateTime, nullable=False)
    endTime = Column(DateTime, nullable=False)

    task = relationship("Task", back_populates="logs")
