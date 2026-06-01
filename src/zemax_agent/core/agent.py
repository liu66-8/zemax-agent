from __future__ import annotations

import json
import logging
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.config import AppConfig
from zemax_agent.core.project import DesignPhase, ProjectMeta
from zemax_agent.core.database import SQLiteStore, SessionRecord
from zemax_agent.core.workflow import WorkflowEngine, DesignContext
from zemax_agent.core.task_scheduler import TaskScheduler, Task, TaskType, TaskStatusEnum
from zemax_agent.core.prompts import get_prompt
from zemax_agent.tools.registry import ToolRegistry
from zemax_agent.llm.provider import LLMProvider, LLMCallResult, OpticalRequirements
from zemax_agent.knowledge.rag import RAGPipeline

logger = logging.getLogger(__name__)


class ActionStep(BaseModel):
    tool_name: str = ""
    tool_params: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class ActionPlan(BaseModel):
    steps: list[ActionStep] = Field(default_factory=list)
    expected_outcome: str = ""
    needs_confirmation: bool = False


class PerformanceSnapshot(BaseModel):
    mtf_avg: Optional[float] = None
    rms_spot_radius: Optional[float] = None
    rms_wavefront: Optional[float] = None
    distortion_max: Optional[float] = None
    merit_function: Optional[float] = None
    seidel_summary: Optional[dict[str, float]] = None


class AgentState(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    project_id: str = ""
    project_name: str = ""
    phase: str = DesignPhase.REQUIREMENTS.value
    design_state: dict[str, Any] = Field(default_factory=dict)
    performance: Optional[PerformanceSnapshot] = None
    action_plan: Optional[ActionPlan] = None
    iteration_count: int = 0
    max_iterations: int = 10
    rag_context: str = ""
    requires_human_input: bool = False
    human_decision: Optional[str] = None
    final_result: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class LangGraphAgent:
    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        rag: Optional[RAGPipeline] = None,
        store: Optional[SQLiteStore] = None,
    ):
        self._llm = llm
        self._tools = tools
        self._rag = rag
        self._store = store
        self._state: Optional[AgentState] = None
        self._stream_callbacks: list[Callable[[str, str], None]] = []
        self._interrupt_event = threading.Event()

    def on_stream(self, callback: Callable[[str, str], None]) -> None:
        self._stream_callbacks.append(callback)

    def _emit(self, event_type: str, data: str) -> None:
        for cb in self._stream_callbacks:
            try:
                cb(event_type, data)
            except Exception:
                pass

    def run(self, task_description: str, project_meta: ProjectMeta, design_context: Optional[DesignContext] = None) -> AgentState:
        state = AgentState(
            messages=[{"role": "user", "content": task_description}],
            project_id=project_meta.id,
            project_name=project_meta.name,
            phase=project_meta.design_phase.value,
        )
        if design_context:
            state.design_state = design_context.model_dump()

        self._state = state
        self._interrupt_event.clear()

        self._emit("status", "perceiving")
        self._perceive()

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            self._emit("status", f"planning_iteration_{state.iteration_count}")

            self._plan()

            if state.requires_human_input:
                self._emit("status", "waiting_for_user")
                return state

            if state.action_plan is None or not state.action_plan.steps:
                self._emit("status", "no_action_plan")
                break

            self._emit("status", "executing")
            self._execute()

            self._emit("status", "evaluating")
            done = self._evaluate()
            if done:
                break

        state.final_result = "Design task completed."
        self._emit("status", "completed")
        return state

    def resume(self, decision: str) -> AgentState:
        if self._state is None:
            raise RuntimeError("No active agent state")

        self._state.requires_human_input = False
        self._state.human_decision = decision
        self._state.messages.append({"role": "user", "content": f"Decision: {decision}"})

        self._emit("status", "executing")
        self._execute()

        self._emit("status", "evaluating")
        self._evaluate()

        self._state.final_result = "Task completed after human review."
        self._emit("status", "completed")
        return self._state

    def cancel(self) -> None:
        self._interrupt_event.set()

    def get_state(self) -> Optional[AgentState]:
        return self._state

    def _perceive(self) -> None:
        state = self._state
        if state is None:
            return

        context_parts = [
            f"Project: {state.project_name}",
            f"Phase: {state.phase}",
        ]
        if state.design_state:
            context_parts.append(f"Design State: {json.dumps(state.design_state, default=str)[:500]}")

        if self._rag:
            try:
                query_text = str(state.messages[-1]["content"]) if state.messages else "optical design"
                retrieval = self._rag.inject_context(
                    query=query_text[:500],
                    top_k=3,
                )
                state.rag_context = retrieval[:1500]
            except Exception:
                state.rag_context = ""

        self._emit("context", "\n".join(context_parts))

    def _plan(self) -> None:
        state = self._state
        if state is None:
            return

        tool_list = self._tools.get_tools_for_llm()

        system_prompt = get_prompt(
            DesignPhase(state.phase) if state.phase else DesignPhase.REQUIREMENTS,
            project_name=state.project_name,
            performance=str(state.performance.model_dump()) if state.performance else "Not yet measured",
            knowledge_context=state.rag_context or "",
        )

        messages = [{"role": "system", "content": system_prompt}] + state.messages[-6:]

        result = self._llm.chat(messages=messages, tools=tool_list, temperature=0.2)

        action_plan = ActionPlan()
        needs_confirmation = False

        if result.tool_calls:
            for tc in result.tool_calls:
                action_plan.steps.append(ActionStep(
                    tool_name=tc["name"],
                    tool_params=tc["arguments"],
                    reason="AI-planned action",
                ))

        if "structural" in result.content.lower() or "delete" in result.content.lower() or "replace" in result.content.lower():
            needs_confirmation = True

        action_plan.needs_confirmation = needs_confirmation
        state.action_plan = action_plan
        state.requires_human_input = needs_confirmation

        if result.content:
            state.messages.append({"role": "assistant", "content": result.content})
            self._emit("message", result.content)

    def _execute(self) -> None:
        state = self._state
        if state is None or state.action_plan is None:
            return

        for step in state.action_plan.steps:
            if self._interrupt_event.is_set():
                break

            self._emit("tool_call", f"{step.tool_name}({json.dumps(step.tool_params)})")

            output = self._tools.invoke(
                tool_name=step.tool_name,
                params=step.tool_params,
                caller="AI",
                session_id=state.project_id,
            )

            if output.success:
                self._emit("tool_result", f"OK: {str(output.data)[:200] if output.data else 'Done'}")
            else:
                self._emit("tool_error", f"Failed: {output.error}")

        state.human_decision = None

    def _evaluate(self) -> bool:
        state = self._state
        if state is None:
            return True

        state.performance = PerformanceSnapshot()

        if state.iteration_count >= state.max_iterations:
            state.messages.append({"role": "system", "content": f"Reached maximum iterations ({state.max_iterations})."})
            return True

        return False
