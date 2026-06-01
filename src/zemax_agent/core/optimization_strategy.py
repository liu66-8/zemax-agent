from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.optimization_monitor import OptimizationMonitor, ConvergenceState
from zemax_agent.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    ADD_VARIABLE = "add_variable"
    REMOVE_VARIABLE = "remove_variable"
    ADJUST_VARIABLE_RANGE = "adjust_variable_range"
    MODIFY_WEIGHT = "modify_weight"
    REPLACE_GLASS = "replace_glass"
    ADD_SURFACE = "add_surface"
    REMOVE_SURFACE = "remove_surface"


class StrategyStep(BaseModel):
    strategy_type: StrategyType
    description: str = ""
    surface_index: Optional[int] = None
    param_code: Optional[int] = None
    new_value: Optional[float] = None
    operand_index: Optional[int] = None
    new_weight: Optional[float] = None
    glass_name: Optional[str] = None
    reason: str = ""


class OptimizationStrategy(BaseModel):
    steps: list[StrategyStep] = Field(default_factory=list)
    reasoning: str = ""
    expected_improvement: str = ""
    risk_level: str = "low"


class StrategyRecord(BaseModel):
    id: str
    strategy: OptimizationStrategy
    mf_before: float
    mf_after: Optional[float] = None
    improvement_pct: Optional[float] = None
    successful: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class OptimizationStrategyAdjuster:
    def __init__(self, llm: Optional[LLMProvider] = None):
        self._llm = llm
        self._history: list[StrategyRecord] = []

    def analyze_and_decide(
        self,
        convergence: ConvergenceState,
        mf_history: list[dict[str, Any]],
        lens_summary: Optional[dict[str, Any]] = None,
        performance: Optional[dict[str, Any]] = None,
    ) -> OptimizationStrategy:
        if convergence.is_stagnant:
            return self._handle_stagnation(convergence, mf_history, lens_summary, performance)
        elif convergence.wall_hit_count >= 5:
            return self._handle_boundary_violations(convergence, mf_history)
        elif convergence.change_rate < 0.001:
            return self._handle_slow_convergence(convergence, mf_history)
        else:
            return OptimizationStrategy(
                steps=[],
                reasoning="Optimization is converging satisfactorily. No strategy adjustment needed.",
                expected_improvement="Continue current course",
                risk_level="low",
            )

    def _handle_stagnation(
        self,
        convergence: ConvergenceState,
        mf_history: list[dict[str, Any]],
        lens_summary: Optional[dict[str, Any]],
        performance: Optional[dict[str, Any]],
    ) -> OptimizationStrategy:
        steps: list[StrategyStep] = []

        if convergence.boundary_violations:
            for v_name in convergence.boundary_violations[:3]:
                steps.append(StrategyStep(
                    strategy_type=StrategyType.ADJUST_VARIABLE_RANGE,
                    description=f"Relax boundary constraint on {v_name}",
                    reason=f"Variable {v_name} repeatedly hitting boundary, restricting optimization.",
                ))

        steps.append(StrategyStep(
            strategy_type=StrategyType.MODIFY_WEIGHT,
            description="Increase weight on underperforming operands",
            reason="Stagnation detected — adjust merit function weights to escape local minimum.",
        ))

        if lens_summary and len(lens_summary.get("surfaces", [])) < 8:
            steps.append(StrategyStep(
                strategy_type=StrategyType.ADD_SURFACE,
                description="Consider adding a surface for additional degrees of freedom",
                reason="Low surface count may limit optimization freedom.",
            ))

        return OptimizationStrategy(
            steps=steps,
            reasoning=(
                f"Stagnation detected after {convergence.stagnation_rounds} rounds "
                f"(change rate: {convergence.change_rate:.2e}). "
                f"Recommend relaxing constraints and adjusting merit function."
            ),
            expected_improvement="Expected 20-40% MF improvement after adjustments",
            risk_level="medium",
        )

    def _handle_boundary_violations(
        self, convergence: ConvergenceState, mf_history: list[dict[str, Any]]
    ) -> OptimizationStrategy:
        steps: list[StrategyStep] = []
        for v_name in convergence.boundary_violations[:5]:
            steps.append(StrategyStep(
                strategy_type=StrategyType.ADJUST_VARIABLE_RANGE,
                description=f"Expand boundary range for {v_name}",
                reason=f"Variable repeatedly hitting bounds — cannot optimize freely.",
            ))

        return OptimizationStrategy(
            steps=steps,
            reasoning=f"{convergence.wall_hit_count} boundary violations detected. Expanding variable ranges.",
            expected_improvement="Unblock optimization convergence",
            risk_level="low",
        )

    def _handle_slow_convergence(
        self, convergence: ConvergenceState, mf_history: list[dict[str, Any]]
    ) -> OptimizationStrategy:
        steps: list[StrategyStep] = [
            StrategyStep(
                strategy_type=StrategyType.MODIFY_WEIGHT,
                description="Redistribute merit function weights toward worst offenders",
                reason="Slow convergence — focus optimization on problematic operands.",
            ),
            StrategyStep(
                strategy_type=StrategyType.REPLACE_GLASS,
                description="Consider glass material optimization",
                reason="Material choice may be limiting performance improvement.",
            ),
        ]

        return OptimizationStrategy(
            steps=steps,
            reasoning="Slow convergence detected. Adjusting optimization approach.",
            expected_improvement="Accelerate convergence by 2-3x",
            risk_level="low",
        )

    def record_result(
        self,
        strategy_id: str,
        strategy: OptimizationStrategy,
        mf_before: float,
        mf_after: float,
    ) -> StrategyRecord:
        improvement = ((mf_before - mf_after) / max(abs(mf_before), 1e-10)) * 100
        record = StrategyRecord(
            id=strategy_id,
            strategy=strategy,
            mf_before=mf_before,
            mf_after=mf_after,
            improvement_pct=round(improvement, 2),
            successful=improvement > 0,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(record)
        return record

    def get_history(self) -> list[StrategyRecord]:
        return list(self._history)

    def get_strategy_summary(self) -> dict[str, Any]:
        if not self._history:
            return {"total_adjustments": 0, "success_rate": 0, "avg_improvement": 0}

        successes = sum(1 for r in self._history if r.successful)
        avg_imp = sum(r.improvement_pct or 0 for r in self._history) / len(self._history)

        return {
            "total_adjustments": len(self._history),
            "success_rate": round(successes / len(self._history) * 100, 1),
            "avg_improvement_pct": round(avg_imp, 2),
        }
