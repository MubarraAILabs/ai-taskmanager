from uuid import uuid4
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.ai_service import AIService


class TaskService:
    def __init__(self, session: Session) -> None:
        self.repository = TaskRepository(session)
        self.ai_service = AIService()

    def list_tasks(self, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.repository.list(skip=skip, limit=limit)

    def get_task(self, task_id: str) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def create_task(self, task_create: TaskCreate) -> Task:
        # Auto-assign priority if not provided
        priority = task_create.priority
        if priority is None:
            priority = self.ai_service.determine_task_priority(
                title=task_create.title,
                description=task_create.description,
                due_date=task_create.due_date
            )

        task = Task(
            id=str(uuid4()),
            title=task_create.title.strip(),
            description=(task_create.description or "").strip(),
            priority=priority,
            status=task_create.status,
            completed=False,
            due_date=task_create.due_date,
        )
        return self.repository.create(task)

    def update_task(self, task_id: str, task_update: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        if task.status == TaskStatus.done:
            task.completed = True

        return self.repository.update(task)

    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        self.repository.delete(task)
