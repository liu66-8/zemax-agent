from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.project import DesignPhase, ProjectMeta

logger = logging.getLogger(__name__)

PHASE_TRANSITIONS: dict[DesignPhase, list[DesignPhase]] = {
    DesignPhase.REQUIREMENTS: [DesignPhase.INITIAL_STRUCTURE],
    DesignPhase.INITIAL_STRUCTURE: [DesignPhase.OPTIMIZATION, DesignPhase.ANALYSIS],
    DesignPhase.OPTIMIZATION: [DesignPhase.ANALYSIS, DesignPhase.INITIAL_STRUCTURE],
    DesignPhase.ANALYSIS: [DesignPhase.OPTIMIZATION, DesignPhase.TOLERANCE, DesignPhase.INITIAL_STRUCTURE],
    DesignPhase.TOLERANCE: [DesignPhase.ANALYSIS, DesignPhase.OPTIMIZATION, DesignPhase.REPORT],
    DesignPhase.REPORT: [DesignPhase.ANALYSIS, DesignPhase.OPTIMIZATION],
}


class DesignContext(BaseModel):
    project_phase: DesignPhase
    project_name: str = ""
    project_description: str = ""
    system_type: str = ""
    lens_summary: Optional[dict[str, Any]] = None
    recent_analyses: list[dict[str, Any]] = Field(default_factory=list)
    recent_tasks: list[dict[str, Any]] = Field(default_factory=list)
    version_count: int = 0
    session_count: int = 0


class WorkflowEngine:
    def __init__(self):
        self._current_phase: Optional[DesignPhase] = None

    @staticmethod
    def get_allowed_transitions(phase: DesignPhase) -> list[DesignPhase]:
        return PHASE_TRANSITIONS.get(phase, [])

    def can_transition(self, from_phase: DesignPhase, to_phase: DesignPhase) -> bool:
        return to_phase in self.get_allowed_transitions(from_phase)

    def transition(
        self, current: DesignPhase, target: DesignPhase
    ) -> tuple[bool, str]:
        if current == target:
            return True, "Already in target phase"

        allowed = self.get_allowed_transitions(current)
        if target not in allowed:
            allowed_names = [p.value for p in allowed]
            return False, f"Cannot transition from {current.value} to {target.value}. Allowed: {allowed_names}"

        self._current_phase = target
        logger.info("Phase transition: %s → %s", current.value, target.value)
        return True, f"Transitioned to {target.value}"

    def build_context(
        self,
        meta: ProjectMeta,
        lens_summary: Optional[dict[str, Any]] = None,
        recent_analyses: Optional[list[dict[str, Any]]] = None,
        recent_tasks: Optional[list[dict[str, Any]]] = None,
        version_count: int = 0,
        session_count: int = 0,
    ) -> DesignContext:
        ctx = DesignContext(
            project_phase=meta.design_phase,
            project_name=meta.name,
            project_description=meta.description,
            system_type=meta.system_type,
            lens_summary=lens_summary,
            recent_analyses=recent_analyses or [],
            recent_tasks=recent_tasks or [],
            version_count=version_count,
            session_count=session_count,
        )
        self._current_phase = meta.design_phase
        return ctx

    def get_current_phase(self) -> Optional[DesignPhase]:
        return self._current_phase

    def suggest_next_phase(self, phase: DesignPhase) -> list[DesignPhase]:
        return self.get_allowed_transitions(phase)
