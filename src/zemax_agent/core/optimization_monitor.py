from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OptimizationTrace(BaseModel):
    iteration: int
    merit_function: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConvergenceState(BaseModel):
    is_stagnant: bool = False
    stagnation_rounds: int = 0
    change_rate: float = 1.0
    wall_hit_count: int = 0
    boundary_violations: list[str] = Field(default_factory=list)


class OptimizationMonitor:
    def __init__(self, stagnation_threshold: int = 5, stagnation_change_rate: float = 1e-4):
        self._stagnation_threshold = stagnation_threshold
        self._stagnation_change_rate = stagnation_change_rate
        self._history: list[OptimizationTrace] = []
        self._boundary_hits: dict[str, int] = {}

    def record(self, iteration: int, merit_function: float) -> OptimizationTrace:
        trace = OptimizationTrace(iteration=iteration, merit_function=merit_function)
        self._history.append(trace)
        return trace

    def record_boundary_hit(self, variable_name: str) -> None:
        self._boundary_hits[variable_name] = self._boundary_hits.get(variable_name, 0) + 1

    def check_convergence(self) -> ConvergenceState:
        wall_hits = sum(self._boundary_hits.values())
        violations = [k for k, v in self._boundary_hits.items() if v >= 3]

        if len(self._history) < 2:
            return ConvergenceState(
                wall_hit_count=wall_hits,
                boundary_violations=violations,
            )

        recent = self._history[-self._stagnation_threshold:]
        if len(recent) < 2:
            return ConvergenceState(
                wall_hit_count=wall_hits,
                boundary_violations=violations,
            )

        first_mf = recent[0].merit_function
        last_mf = recent[-1].merit_function
        change_rate = abs(last_mf - first_mf) / max(abs(first_mf), 1e-10)

        is_stagnant = (
            change_rate < self._stagnation_change_rate
            and len(recent) >= self._stagnation_threshold
        )

        wall_hits = sum(self._boundary_hits.values())
        violations = [k for k, v in self._boundary_hits.items() if v >= 3]

        return ConvergenceState(
            is_stagnant=is_stagnant,
            stagnation_rounds=len(recent) if is_stagnant else 0,
            change_rate=change_rate,
            wall_hit_count=wall_hits,
            boundary_violations=violations,
        )

    def get_trend(self) -> list[dict[str, Any]]:
        return [
            {"iteration": t.iteration, "merit_function": t.merit_function, "timestamp": t.timestamp}
            for t in self._history
        ]

    def get_summary(self) -> dict[str, Any]:
        if not self._history:
            return {"iterations": 0, "initial_mf": None, "final_mf": None, "improvement_pct": 0}

        initial = self._history[0].merit_function
        final = self._history[-1].merit_function
        improvement = ((initial - final) / max(abs(initial), 1e-10)) * 100 if initial else 0

        return {
            "iterations": len(self._history),
            "initial_mf": initial,
            "final_mf": final,
            "improvement_pct": round(improvement, 2),
            "convergence": self.check_convergence().model_dump(),
        }

    def reset(self) -> None:
        self._history.clear()
        self._boundary_hits.clear()
