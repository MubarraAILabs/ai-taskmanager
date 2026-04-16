from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    AITaskGenerationRequest,
    AITaskGenerationResponse,
    AITaskSummaryRequest,
    AITaskSummaryResponse,
    AgentWorkflowRequest,
    AgentWorkflowResponse,
)
from app.services.task_service import TaskService
from app.services.ai_service import AIService
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/tasks", tags=["tasks"])
ai_router = APIRouter(prefix="/ai", tags=["ai"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[TaskResponse])
def read_tasks(
    skip: int = 0,
    limit: int = Query(100, le=100, gt=0),
    db: Session = Depends(get_db),
):
    return TaskService(db).list_tasks(skip=skip, limit=limit)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_create: TaskCreate, db: Session = Depends(get_db)):
    return TaskService(db).create_task(task_create)


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: str, db: Session = Depends(get_db)):
    return TaskService(db).get_task(task_id)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    return TaskService(db).update_task(task_id, task_update)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    TaskService(db).delete_task(task_id)


@ai_router.post("/generate-tasks", response_model=AITaskGenerationResponse)
def generate_tasks(request: AITaskGenerationRequest):
    """Generate structured tasks from a goal using AI."""
    ai_service = AIService()
    return ai_service.generate_tasks_from_goal(request.goal)


@ai_router.post("/summarize", response_model=AITaskSummaryResponse)
def summarize_tasks(request: AITaskSummaryRequest):
    """Summarize a list of tasks and return a daily plan."""
    ai_service = AIService(require_api=False)
    return ai_service.summarize_tasks(request.tasks)


@ai_router.post("/workflow", response_model=AgentWorkflowResponse)
async def execute_workflow(request: AgentWorkflowRequest, db: Session = Depends(get_db)):
    """
    Execute the complete agent workflow:
    1. Take user goal
    2. Generate tasks
    3. Prioritize tasks
    4. Store in database
    5. Return execution plan
    """
    workflow = WorkflowService(db)
    return await workflow.execute_goal_workflow(request.goal)
