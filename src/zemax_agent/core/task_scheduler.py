from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.database import SQLiteStore, TaskRecord
from zemax_agent.core.project import DesignPhase

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    LENS_EDIT = "lens_edit"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    TOLERANCE = "tolerance"
    SYSTEM = "system"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    task_type: TaskType
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    params: dict[str, Any] = Field(default_factory=dict)
    progress: float = 0.0
    progress_message: str = ""
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    on_progress: Any = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True


class TaskScheduler:
    def __init__(self, store: SQLiteStore):
        self._store = store
        self._pending: list[Task] = []
        self._running: Optional[Task] = None
        self._callback: Any = None

    def set_progress_callback(self, callback: Any) -> None:
        self._callback = callback

    def submit(self, task: Task) -> Task:
        self._store.create_task(TaskRecord(
            id=task.id, project_id=task.project_id,
            task_type=task.task_type.value, status=task.status.value,
            params=task.params, progress=task.progress,
            created_at=task.created_at,
        ))
        self._pending.append(task)
        logger.info("Task submitted: %s (%s)", task.task_type.value, task.id[:8])
        return task

    def start_next(self) -> Optional[Task]:
        if self._running is not None:
            return None
        if not self._pending:
            return None

        self._running = self._pending.pop(0)
        self._running.status = TaskStatusEnum.RUNNING
        self._running.started_at = datetime.now(timezone.utc).isoformat()
        self._store.update_task(
            self._running.id,
            status=self._running.status.value,
            started_at=self._running.started_at,
        )
        logger.info("Task started: %s (%s)", self._running.task_type.value, self._running.id[:8])
        return self._running

    def update_progress(self, progress: float, message: str = "") -> None:
        if self._running is None:
            return
        self._running.progress = min(100.0, max(0.0, progress))
        self._running.progress_message = message
        self._store.update_task(self._running.id, progress=progress)
        if self._callback:
            try:
                self._callback(self._running.id, progress, message)
            except Exception:
                pass

    def complete_current(self, result: Optional[dict[str, Any]] = None) -> Optional[Task]:
        if self._running is None:
            return None
        self._running.status = TaskStatusEnum.COMPLETED
        self._running.completed_at = datetime.now(timezone.utc).isoformat()
        self._running.progress = 100.0
        self._running.result = result
        self._store.update_task(
            self._running.id,
            status=self._running.status.value,
            completed_at=self._running.completed_at,
            progress=100.0,
            result=result,
        )
        logger.info("Task completed: %s (%s)", self._running.task_type.value, self._running.id[:8])
        finished = self._running
        self._running = None
        return finished

    def fail_current(self, error: str) -> Optional[Task]:
        if self._running is None:
            return None
        self._running.status = TaskStatusEnum.FAILED
        self._running.completed_at = datetime.now(timezone.utc).isoformat()
        self._running.error = error
        self._store.update_task(
            self._running.id,
            status=self._running.status.value,
            completed_at=self._running.completed_at,
            error=error,
        )
        logger.error("Task failed: %s (%s) - %s", self._running.task_type.value, self._running.id[:8], error)
        failed = self._running
        self._running = None
        return failed

    def cancel(self, task_id: str) -> bool:
        for i, task in enumerate(self._pending):
            if task.id == task_id:
                task.status = TaskStatusEnum.CANCELLED
                self._store.update_task(task.id, status=TaskStatusEnum.CANCELLED.value)
                self._pending.pop(i)
                return True
        if self._running and self._running.id == task_id:
            self._running.status = TaskStatusEnum.CANCELLED
            self._store.update_task(self._running.id, status=TaskStatusEnum.CANCELLED.value)
            self._running = None
            return True
        return False

    def cancel_all_pending(self) -> int:
        count = 0
        for task in self._pending:
            task.status = TaskStatusEnum.CANCELLED
            self._store.update_task(task.id, status=TaskStatusEnum.CANCELLED.value)
            count += 1
        self._pending.clear()
        return count

    @property
    def running_task(self) -> Optional[Task]:
        return self._running

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def get_queue_status(self) -> dict[str, Any]:
        return {
            "running": self._running.model_dump(exclude={"on_progress"}) if self._running else None,
            "pending_count": len(self._pending),
            "pending_tasks": [t.model_dump(exclude={"on_progress"}) for t in self._pending],
        }

    def get_history(
        self, project_id: str, task_type: Optional[str] = None, status: Optional[str] = None, limit: int = 50
    ) -> list[TaskRecord]:
        return self._store.list_tasks(project_id=project_id, task_type=task_type, status=status, limit=limit)
