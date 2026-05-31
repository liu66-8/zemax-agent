from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.exceptions import ZOSError, ZOSNotConnectedError, RETRYABLE_TYPES

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass(order=True)
class ZOSTask:
    priority: int
    seq: int
    task_id: str = field(compare=False)
    task_type: str = field(compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    result: Any = field(default=None, compare=False)
    error: Optional[str] = field(default=None, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    started_at: Optional[float] = field(default=None, compare=False)
    completed_at: Optional[float] = field(default=None, compare=False)
    on_progress: Optional[Callable[[float, str], None]] = field(default=None, compare=False, repr=False)


class ZOSDispatcher:
    _instance: Optional["ZOSDispatcher"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ZOSDispatcher":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, connection_mode: str = "standalone", max_retries: int = 3):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._connection = ZOSConnection(mode=connection_mode)
        self._max_retries = max_retries
        self._queue: deque[ZOSTask] = deque()
        self._seq_counter: int = 0
        self._condition = threading.Condition()
        self._running = False
        self._worker: Optional[threading.Thread] = None
        self._current_task: Optional[ZOSTask] = None
        self._progress_callbacks: dict[str, Callable] = {}

    @classmethod
    def get_instance(cls) -> "ZOSDispatcher":
        if cls._instance is None:
            raise RuntimeError("ZOSDispatcher not initialized")
        return cls._instance

    def connect(self, timeout: float = 30.0) -> None:
        self._connection.connect(timeout)
        self._running = True
        self._worker = threading.Thread(target=self._process_queue, daemon=True, name="ZOSDispatcher")
        self._worker.start()
        logger.info("ZOSDispatcher started")

    def disconnect(self) -> None:
        self._running = False
        with self._condition:
            self._condition.notify_all()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=10.0)
        self._connection.disconnect()
        logger.info("ZOSDispatcher stopped")

    @property
    def is_connected(self) -> bool:
        return self._connection.is_connected

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def current_task(self) -> Optional[ZOSTask]:
        return self._current_task

    def submit(
        self,
        task_type: str,
        func: Callable,
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        on_progress: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> ZOSTask:
        if not self.is_connected and task_type != "system.connect":
            raise ZOSNotConnectedError("Cannot submit task: not connected to OpticStudio")

        with self._lock:
            self._seq_counter += 1
            seq = self._seq_counter

        task = ZOSTask(
            priority=priority.value,
            seq=seq,
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            func=func,
            args=args,
            kwargs=kwargs,
            on_progress=on_progress,
        )

        with self._condition:
            self._queue.append(task)
            self._queue = deque(sorted(self._queue, key=lambda t: (-t.priority, t.seq)))
            self._condition.notify()
            logger.debug("Task submitted: %s (%s)", task.task_type, task.task_id[:8])

        return task

    def cancel(self, task_id: str) -> bool:
        with self._condition:
            if self._current_task and self._current_task.task_id == task_id:
                self._current_task.status = TaskStatus.CANCELLED
                return True
            for task in self._queue:
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELLED
                    self._queue.remove(task)
                    return True
        return False

    def cancel_all_pending(self) -> int:
        count = 0
        with self._condition:
            for task in list(self._queue):
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    self._queue.remove(task)
                    count += 1
        return count

    def get_task(self, task_id: str) -> Optional[ZOSTask]:
        if self._current_task and self._current_task.task_id == task_id:
            return self._current_task
        for task in self._queue:
            if task.task_id == task_id:
                return task
        return None

    def get_queue_status(self) -> dict[str, Any]:
        return {
            "connected": self.is_connected,
            "queue_size": self.queue_size,
            "current_task": self._current_task.task_type if self._current_task else None,
            "current_task_id": self._current_task.task_id if self._current_task else None,
        }

    def submit_and_wait(
        self,
        task_type: str,
        func: Callable,
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        on_progress: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> Any:
        result_holder: dict[str, Any] = {}
        error_holder: dict[str, Any] = {}
        event = threading.Event()

        def wrapped(*a: Any, **kw: Any) -> Any:
            try:
                result_holder["value"] = func(*a, **kw)
            except Exception as e:
                error_holder["error"] = e
            finally:
                event.set()
            return result_holder.get("value")

        task = self.submit(task_type, wrapped, *args, priority=priority, on_progress=on_progress, **kwargs)

        if not event.wait(timeout=timeout):
            raise ZOSError(f"Task {task_type} timed out after {timeout}s")

        if "error" in error_holder:
            raise error_holder["error"]

        return result_holder.get("value")

    def _process_queue(self) -> None:
        while self._running:
            with self._condition:
                pending = [t for t in self._queue if t.status == TaskStatus.PENDING]
                if not pending:
                    self._condition.wait(timeout=1.0)
                    continue
                task = pending[0]
                self._queue.remove(task)
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                self._current_task = task

            retries = 0
            while retries <= self._max_retries:
                try:
                    task.result = task.func(*task.args, **task.kwargs)
                    task.status = TaskStatus.COMPLETED
                    break
                except RETRYABLE_TYPES:
                    retries += 1
                    if retries > self._max_retries:
                        task.error = f"Failed after {self._max_retries} retries"
                        task.status = TaskStatus.FAILED
                        logger.error("Task %s failed after %d retries", task.task_type, self._max_retries)
                    else:
                        logger.warning("Task %s retry %d/%d", task.task_type, retries, self._max_retries)
                        time.sleep(min(2 ** retries, 30))
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    logger.error("Task %s failed: %s", task.task_type, e)
                    break

            task.completed_at = time.time()
            self._current_task = None
