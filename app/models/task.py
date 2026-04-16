import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(length=36), primary_key=True, index=True)
    title = Column(String(length=255), nullable=False)
    description = Column(Text, default="")
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.todo)
    completed = Column(Boolean, nullable=False, default=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
