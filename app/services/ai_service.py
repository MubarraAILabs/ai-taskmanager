import json
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from groq import Groq

from app.core.config import get_settings
from app.schemas.task import AITaskGenerationResponse, AITaskSummaryResponse, GeneratedTask, TaskPriority


class AIService:
    def __init__(self, require_api: bool = True):
        settings = get_settings()
        self.client = None
        if settings.groq_api_key:
            self.client = Groq(api_key=settings.groq_api_key)

        if require_api and self.client is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Groq API key not configured"
            )

    def generate_tasks_from_goal(self, goal: str) -> AITaskGenerationResponse:
        normalized_goal = goal.strip()
        if not normalized_goal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Goal cannot be empty"
            )

        try:
            prompt = f"""
            Goal: {goal}

            Break this goal into 3-8 specific, actionable tasks. Return the response as a JSON array of tasks with the exact structure:

            [
                {{
                    "title": "string",
                    "description": "string",
                    "priority": "low|medium|high",
                    "estimated_time_hours": number
                }}
            ]

            Guidelines:
            - Create 3-8 tasks that are specific and actionable
            - Tasks should be ordered logically (dependencies first)
            - Prioritize based on impact and urgency
            - Time estimates should be realistic for a skilled professional
            - Include both high-level planning and detailed execution tasks
            """

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a task breakdown expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Try to parse the JSON response
            try:
                tasks_data = json.loads(content)
                if not isinstance(tasks_data, list):
                    raise ValueError("Response is not a list")
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback: try to extract JSON from the response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    tasks_data = json.loads(json_match.group())
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to parse AI response as JSON"
                    )

            # Validate and convert to GeneratedTask objects
            tasks: List[GeneratedTask] = []
            for task_data in tasks_data:
                try:
                    task = GeneratedTask(**task_data)
                    tasks.append(task)
                except Exception as e:
                    # Skip invalid tasks but continue processing
                    continue

            if not tasks:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No valid tasks generated"
                )

            return AITaskGenerationResponse(
                goal=goal,
                tasks=tasks,
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task generation failed: {str(e)}"
            )

    def determine_task_priority(self, title: str, description: str = "", due_date: Optional[datetime] = None) -> TaskPriority:
        """Determine task priority based on urgency and importance using AI."""
        try:
            # Calculate urgency based on due date
            urgency = "low"
            if due_date:
                days_until_due = (due_date - datetime.utcnow()).days
                if days_until_due <= 1:
                    urgency = "high"
                elif days_until_due <= 3:
                    urgency = "medium"

            prompt = f"""
            Analyze this task and determine its priority (high, medium, or low) based on urgency and importance.

            Task Title: {title}
            Task Description: {description or "No description provided"}
            Urgency (based on due date): {urgency}

            Consider:
            - Impact: How important is this task to overall goals?
            - Urgency: How time-sensitive is this task?
            - Complexity: How much effort is required?

            Respond with only one word: "high", "medium", or "low"
            """

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a task prioritization expert. Respond with only: high, medium, or low."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3
            )

            priority_str = response.choices[0].message.content.strip().lower()

            # Map response to enum
            if priority_str == "high":
                return TaskPriority.high
            elif priority_str == "medium":
                return TaskPriority.medium
            else:
                return TaskPriority.low

        except Exception as e:
            # Fallback to medium priority if AI fails
            return TaskPriority.medium

    def summarize_tasks(self, tasks: List[dict]) -> "AITaskSummaryResponse":
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one task is required for summarization"
            )

        task_items = []
        for task in tasks:
            if hasattr(task, "dict"):
                task_items.append(task.dict())
            else:
                task_items.append(task)

        total_tasks = len(task_items)
        priority_counts = Counter(
            str(task.get("priority", "medium")).lower() for task in task_items
        )
        status_counts = Counter(
            str(task.get("status", "todo")).lower() for task in task_items
        )

        high_priority = priority_counts.get("high", 0)
        medium_priority = priority_counts.get("medium", 0)
        low_priority = priority_counts.get("low", 0)

        upcoming = []
        for task in task_items:
            due_date = task.get("due_date")
            if due_date:
                try:
                    parsed_due = datetime.fromisoformat(due_date)
                except ValueError:
                    continue
                if parsed_due <= datetime.utcnow() + timedelta(days=2):
                    upcoming.append(task)

        priority_summary = (
            f"{high_priority} high, {medium_priority} medium, {low_priority} low priorities"
        )
        status_summary = ", ".join(
            f"{count} {state}" for state, count in status_counts.items()
        ) or "no status data"

        summary_parts = [
            f"Summary for {total_tasks} tasks:",
            f"Priority breakdown: {priority_summary}.",
            f"Status breakdown: {status_summary}.",
        ]

        if upcoming:
            summary_parts.append(
                f"{len(upcoming)} task(s) are due within 2 days and should be prioritized first."
            )

        summary_text = " ".join(summary_parts)

        sorted_tasks = sorted(
            task_items,
            key=lambda task: (
                0 if str(task.get("priority", "medium")).lower() == "high" else 1,
                0 if task.get("due_date") else 1,
                task.get("due_date") or ""
            )
        )

        daily_plan = []
        for task in sorted_tasks[:5]:
            title = task.get("title", "Untitled task")
            priority = str(task.get("priority", "medium")).lower()
            due = task.get("due_date")
            line = f"{title} ({priority} priority)"
            if due:
                line += f" — due {due}"
            daily_plan.append(line)

        return AITaskSummaryResponse(summary=summary_text, daily_plan=daily_plan)
