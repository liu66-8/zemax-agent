from pathlib import Path

from zemax_agent.core.database import SQLiteStore, ProjectRecord
from zemax_agent.core.project import DesignPhase, ProjectMeta
from zemax_agent.core.workflow import WorkflowEngine
from zemax_agent.core.prompts import PROMPT_TEMPLATES, get_prompt, get_system_prompt
from zemax_agent.core.agent import LangGraphAgent, AgentState, ActionPlan, ActionStep
from zemax_agent.core.ipc import IPCRouter, IPCMessage
from zemax_agent.core.config import LLMConfig
from zemax_agent.llm.provider import LLMProvider
from zemax_agent.tools.registry import ToolRegistry


class TestPromptTemplates:
    def test_all_phases_have_template(self):
        phase_keys = {
            DesignPhase.REQUIREMENTS.value: "requirement_analysis",
            DesignPhase.INITIAL_STRUCTURE.value: "initial_structure",
            DesignPhase.OPTIMIZATION.value: "optimization",
            DesignPhase.ANALYSIS.value: "diagnosis",
            DesignPhase.TOLERANCE.value: "diagnosis",
            DesignPhase.REPORT.value: "report",
        }
        for phase in DesignPhase:
            key = phase_keys.get(phase.value, phase.value)
            template = PROMPT_TEMPLATES.get(key)
            assert template is not None, f"No template key for {phase.value} (looked up: {key})"

    def test_get_prompt_renders(self):
        prompt = get_prompt(
            "optimization",
            project_name="Test Lens",
            performance="MTF: 0.7",
            knowledge_context="Use BK7 glass",
        )
        assert "Test Lens" in prompt
        assert "MTF" in prompt

    def test_get_system_prompt(self):
        prompt = get_system_prompt(DesignPhase.REQUIREMENTS, project_name="Test")
        assert "optical engineering" in prompt.lower()


class TestAgentState:
    def test_default_state(self):
        state = AgentState()
        assert state.phase == DesignPhase.REQUIREMENTS.value
        assert state.iteration_count == 0
        assert state.max_iterations == 10

    def test_action_plan(self):
        plan = ActionPlan(
            steps=[
                ActionStep(tool_name="lens.get_surface_data", tool_params={"surface_index": 1}),
                ActionStep(tool_name="analysis.get_mtf", tool_params={"frequency": 30.0}),
            ],
            expected_outcome="Get current lens state and MTF",
            needs_confirmation=False,
        )
        assert len(plan.steps) == 2
        assert plan.steps[0].tool_name == "lens.get_surface_data"


class TestIPCRouter:
    def test_handle_request(self):
        router = IPCRouter()
        router.register_handler("ping", lambda: "pong")

        msg = router.handle_message('{"type":"request","id":"1","command":"ping","params":{}}')
        assert msg is not None
        assert msg.type == "response"
        assert msg.data == "pong"

    def test_handle_unknown_command(self):
        router = IPCRouter()
        msg = router.handle_message('{"type":"request","id":"1","command":"unknown","params":{}}')
        assert msg is not None
        assert msg.error == "Unknown command: unknown"

    def test_send_progress(self):
        router = IPCRouter()
        msg = router.send_progress(75.0, "Almost done")
        assert msg.progress == 75.0
        assert msg.message == "Almost done"

    def test_send_event(self):
        router = IPCRouter()
        msg = router.send_event("status_change", {"phase": "optimization"})
        assert msg.type == "event"
        assert msg.command == "status_change"

    def test_event_listener(self):
        router = IPCRouter()
        events = []

        router.on_event("test_event", lambda data: events.append(data))
        router._emit("test_event", {"key": "value"})

        assert len(events) == 1
        assert events[0]["key"] == "value"
