from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    ZOS = "zos"
    QDRANT = "qdrant"
    SQLITE = "sqlite"
    PYTHON = "python"


@dataclass
class ComponentHealth:
    component: ComponentType
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    last_check: float = 0.0
    latency_ms: float = 0.0


@dataclass
class SystemHealth:
    overall: HealthStatus = HealthStatus.UNKNOWN
    components: dict[str, ComponentHealth] = field(default_factory=dict)
    timestamp: float = 0.0


class HealthMonitor:
    def __init__(self, check_interval: float = 30.0):
        self._interval = check_interval
        self._components: dict[str, ComponentHealth] = {}
        self._checks: dict[str, Callable[[], tuple[bool, str]]] = {}
        self._callbacks: list[Callable[[SystemHealth], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

        for ct in ComponentType:
            self._components[ct.value] = ComponentHealth(component=ct)

    def register_check(self, component: ComponentType, check_fn: Callable[[], tuple[bool, str]]) -> None:
        self._checks[component.value] = check_fn

    def on_health_change(self, callback: Callable[[SystemHealth], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="HealthMonitor")
        self._thread.start()
        logger.info("HealthMonitor started (interval=%.0fs)", self._interval)

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("HealthMonitor stopped")

    def _loop(self) -> None:
        while self._running:
            self.check_now()
            time.sleep(self._interval)

    def check_now(self) -> SystemHealth:
        now = time.time()
        previous = {
            k: v.status
            for k, v in self._components.items()
        }

        for key, check_fn in self._checks.items():
            start = time.perf_counter()
            try:
                ok, msg = check_fn()
                latency = (time.perf_counter() - start) * 1000
                self._components[key].status = HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY
                self._components[key].message = msg
                self._components[key].latency_ms = latency
            except Exception as e:
                self._components[key].status = HealthStatus.UNHEALTHY
                self._components[key].message = str(e)

            self._components[key].last_check = now

        statuses = [self._components[k].status for k in self._checks.keys() if k in self._components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        health = SystemHealth(
            overall=overall,
            components=dict(self._components),
            timestamp=now,
        )

        changed = any(
            previous.get(k) != v.status
            for k, v in self._components.items()
        )
        if changed:
            for cb in self._callbacks:
                try:
                    cb(health)
                except Exception:
                    pass

        return health

    def get_status(self) -> SystemHealth:
        return SystemHealth(
            overall=self._get_overall(),
            components=dict(self._components),
            timestamp=time.time(),
        )

    def _get_overall(self) -> HealthStatus:
        registered = {k for k in self._checks.keys()}
        if not registered:
            return HealthStatus.UNKNOWN
        statuses = [self._components[k].status for k in registered if k in self._components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        return HealthStatus.DEGRADED
