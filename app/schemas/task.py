from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: TaskPriority = TaskPriority.medium
    status: TaskStatus = TaskStatus.todo
    due_date: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: Optional[TaskPriority] = None  # Will be auto-assigned if not provided
    status: TaskStatus = TaskStatus.todo
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# AI Task Generation Schemas
class AITaskGenerationRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000, description="The goal to break down into tasks")


class GeneratedTask(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1024)
    priority: TaskPriority
    estimated_time_hours: float = Field(..., gt=0, le=168)  # Max 1 week


class AITaskGenerationResponse(BaseModel):
    goal: str
    tasks: List[GeneratedTask]
    generated_at: datetime


class AITaskSummaryRequest(BaseModel):
    tasks: List[TaskBase] = Field(..., min_items=1, description="Tasks to summarize")


class AITaskSummaryResponse(BaseModel):
    summary: str
    daily_plan: List[str]


class AgentWorkflowRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000, description="User goal to execute")


class WorkflowExecutionStep(BaseModel):
    step: int
    name: str
    status: str
    details: Optional[str] = None


class AgentWorkflowResponse(BaseModel):
    goal: str
    execution_steps: List[WorkflowExecutionStep]
    generated_tasks: List[TaskResponse]
    execution_plan: List[str]
    total_estimated_hours: float
