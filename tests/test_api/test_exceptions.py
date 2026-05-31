"""Tests for exception type hierarchy."""

from __future__ import annotations

from zemax_agent.api.exceptions import (
    KnowledgeConstraintError,
    LLMError,
    PhysicsViolationError,
    ToolExecutionError,
    ValidationError,
    ZemaxAgentError,
    ZOSAnalysisError,
    ZOSConnectionError,
    ZOSOperationError,
    ZOSOptimizationError,
)


class TestExceptionInstantiation:
    """测试所有异常类可正常实例化。"""

    def test_zemax_agent_error(self) -> None:
        exc = ZemaxAgentError("test message")
        assert str(exc) == "test message"
        assert isinstance(exc, Exception)

    def test_zos_connection_error(self) -> None:
        exc = ZOSConnectionError("connection failed")
        assert str(exc) == "connection failed"

    def test_zos_operation_error(self) -> None:
        exc = ZOSOperationError("operation failed")
        assert str(exc) == "operation failed"

    def test_zos_analysis_error(self) -> None:
        exc = ZOSAnalysisError("analysis failed")
        assert str(exc) == "analysis failed"

    def test_zos_optimization_error(self) -> None:
        exc = ZOSOptimizationError("optimization failed")
        assert str(exc) == "optimization failed"

    def test_validation_error(self) -> None:
        exc = ValidationError("validation failed")
        assert str(exc) == "validation failed"

    def test_physics_violation_error(self) -> None:
        exc = PhysicsViolationError("physics violation")
        assert str(exc) == "physics violation"

    def test_knowledge_constraint_error(self) -> None:
        exc = KnowledgeConstraintError("knowledge constraint")
        assert str(exc) == "knowledge constraint"

    def test_tool_execution_error(self) -> None:
        exc = ToolExecutionError("tool execution failed")
        assert str(exc) == "tool execution failed"

    def test_llm_error(self) -> None:
        exc = LLMError("llm error")
        assert str(exc) == "llm error"


class TestExceptionInheritance:
    """测试异常类的继承关系。"""

    def test_zos_connection_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ZOSConnectionError, ZemaxAgentError)
        assert issubclass(ZOSConnectionError, Exception)

    def test_zos_operation_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ZOSOperationError, ZemaxAgentError)

    def test_zos_analysis_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ZOSAnalysisError, ZemaxAgentError)

    def test_zos_optimization_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ZOSOptimizationError, ZemaxAgentError)

    def test_validation_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ValidationError, ZemaxAgentError)

    def test_physics_violation_is_validation_and_zemax(self) -> None:
        assert issubclass(PhysicsViolationError, ValidationError)
        assert issubclass(PhysicsViolationError, ZemaxAgentError)

    def test_knowledge_constraint_is_validation_and_zemax(self) -> None:
        assert issubclass(KnowledgeConstraintError, ValidationError)
        assert issubclass(KnowledgeConstraintError, ZemaxAgentError)

    def test_tool_execution_error_is_zemax_agent_error(self) -> None:
        assert issubclass(ToolExecutionError, ZemaxAgentError)

    def test_llm_error_is_zemax_agent_error(self) -> None:
        assert issubclass(LLMError, ZemaxAgentError)


class TestExceptionMessagePropagation:
    """测试异常消息传递。"""

    def test_message_preserved_through_catch(self) -> None:
        try:
            raise ZOSConnectionError("test message 123")
        except ZemaxAgentError as e:
            assert str(e) == "test message 123"

    def test_sub_exception_caught_as_parent(self) -> None:
        try:
            raise PhysicsViolationError("phys violated")
        except ValidationError as e:
            assert str(e) == "phys violated"

    def test_sub_sub_exception_caught_as_root(self) -> None:
        try:
            raise PhysicsViolationError("phys violated")
        except ZemaxAgentError as e:
            assert str(e) == "phys violated"

    def test_no_arg_exception(self) -> None:
        exc = ZemaxAgentError()
        assert str(exc) == ""
