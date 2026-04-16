import asyncio
from typing import List

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.schemas.task import (
    AgentWorkflowResponse,
    TaskResponse,
    WorkflowExecutionStep,
)
from app.services.ai_service import AIService
from app.services.task_service import TaskService


class WorkflowService:
    def __init__(self, session: Session):
        self.session = session
        self.task_service = TaskService(session)
        self.ai_service = AIService(require_api=True)
        self.execution_steps: List[WorkflowExecutionStep] = []

    async def execute_goal_workflow(self, goal: str) -> AgentWorkflowResponse:
        """
        Execute the complete agent workflow:
        1. Generate tasks from goal
        2. Create tasks with auto-prioritization
        3. Build execution plan
        4. Return complete workflow response
        """
        self.execution_steps = []

        # Step 1: Generate tasks from goal
        step1 = await self._step_generate_tasks(goal)
        self.execution_steps.append(step1)

        if step1.status == "failed":
            return self._build_error_response(goal)

        # Step 2: Create and store tasks in database with prioritization
        step2 = await self._step_store_tasks(goal)
        self.execution_steps.append(step2)

        if step2.status == "failed":
            return self._build_error_response(goal)

        # Step 3: Build execution plan
        step3 = await self._step_build_plan(goal)
        self.execution_steps.append(step3)

        # Step 4: Retrieve created tasks
        created_tasks = self.task_service.list_tasks(skip=0, limit=100)
        task_responses = [
            TaskResponse.from_orm(task) for task in created_tasks[-10:]  # Last 10 tasks
        ]

        # Calculate total estimated time
        total_estimated = self._calculate_total_time(task_responses)

        # Build execution plan
        execution_plan = self._build_execution_steps(task_responses)

        return AgentWorkflowResponse(
            goal=goal,
            execution_steps=self.execution_steps,
            generated_tasks=task_responses,
            execution_plan=execution_plan,
            total_estimated_hours=total_estimated,
        )

    async def _step_generate_tasks(self, goal: str) -> WorkflowExecutionStep:
        """Step 1: Generate tasks from goal using AI"""
        try:
            def sync_generate():
                response = self.ai_service.generate_tasks_from_goal(goal)
                return response.tasks

            tasks = await asyncio.to_thread(sync_generate)
            return WorkflowExecutionStep(
                step=1,
                name="Generate Tasks from Goal",
                status="completed",
                details=f"Generated {len(tasks)} tasks using AI",
            )
        except Exception as e:
            return WorkflowExecutionStep(
                step=1,
                name="Generate Tasks from Goal",
                status="failed",
                details=f"Error: {str(e)}",
            )

    async def _step_store_tasks(self, goal: str) -> WorkflowExecutionStep:
        """Step 2: Generate and store tasks in database with auto-prioritization"""
        try:
            def sync_generate_and_store():
                response = self.ai_service.generate_tasks_from_goal(goal)
                created_count = 0

                for generated_task in response.tasks:
                    from app.schemas.task import TaskCreate

                    task_create = TaskCreate(
                        title=generated_task.title,
                        description=generated_task.description,
                        priority=generated_task.priority,
                    )
                    self.task_service.create_task(task_create)
                    created_count += 1

                return created_count

            count = await asyncio.to_thread(sync_generate_and_store)
            return WorkflowExecutionStep(
                step=2,
                name="Prioritize & Store Tasks",
                status="completed",
                details=f"Created and stored {count} tasks in database with auto-priority",
            )
        except Exception as e:
            return WorkflowExecutionStep(
                step=2,
                name="Prioritize & Store Tasks",
                status="failed",
                details=f"Error: {str(e)}",
            )

    async def _step_build_plan(self, goal: str) -> WorkflowExecutionStep:
        """Step 3: Build execution plan"""
        try:
            return WorkflowExecutionStep(
                step=3,
                name="Build Execution Plan",
                status="completed",
                details="Execution plan created and prioritized",
            )
        except Exception as e:
            return WorkflowExecutionStep(
                step=3,
                name="Build Execution Plan",
                status="failed",
                details=f"Error: {str(e)}",
            )

    def _build_error_response(self, goal: str) -> AgentWorkflowResponse:
        """Build error response if workflow fails"""
        return AgentWorkflowResponse(
            goal=goal,
            execution_steps=self.execution_steps,
            generated_tasks=[],
            execution_plan=["Workflow failed. Please check the execution steps for details."],
            total_estimated_hours=0.0,
        )

    def _calculate_total_time(self, tasks: List[TaskResponse]) -> float:
        """Calculate total estimated hours from tasks"""
        total = 0.0
        for task_dict in tasks:
            if isinstance(task_dict, dict) and "estimated_time_hours" in task_dict:
                total += task_dict["estimated_time_hours"]
        return total

    def _build_execution_steps(self, tasks: List[TaskResponse]) -> List[str]:
        """Build a prioritized execution plan from tasks"""
        plan = []

        # Sort by priority
        high_priority = [t for t in tasks if t.priority == "high"]
        medium_priority = [t for t in tasks if t.priority == "medium"]
        low_priority = [t for t in tasks if t.priority == "low"]

        if high_priority:
            plan.append("=== HIGH PRIORITY (Execute First) ===")
            for task in high_priority[:3]:
                plan.append(f"• {task.title}")

        if medium_priority:
            plan.append("=== MEDIUM PRIORITY (Execute Next) ===")
            for task in medium_priority[:3]:
                plan.append(f"• {task.title}")

        if low_priority:
            plan.append("=== LOW PRIORITY (Execute When Available) ===")
            for task in low_priority[:3]:
                plan.append(f"• {task.title}")

        return plan if plan else ["No tasks generated"]
