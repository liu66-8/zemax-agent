"""ZOS-API wrapper layer.

Provides a clean Python interface to Zemax OpticStudio's ZOS-API,
handling connection lifecycle, command execution, and data retrieval.
"""

from __future__ import annotations

from .analysis import ZemaxAnalysis
from .exceptions import (
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
from .lde import GlassCatalog, SurfaceType, ZemaxLDE
from .optimization import MeritOperand, ZemaxOptimizer
from .retry import retry_on_failure, with_connection_retry, with_llm_retry
from .system_settings import ApertureType, FieldType, ZemaxSystemSettings
from .transaction import OperationBatch, OperationResult, TransactionResult

__all__ = [
    "ZemaxAgentError",
    "ZOSConnectionError",
    "ZOSOperationError",
    "ZOSAnalysisError",
    "ZOSOptimizationError",
    "ValidationError",
    "PhysicsViolationError",
    "KnowledgeConstraintError",
    "ToolExecutionError",
    "LLMError",
    "retry_on_failure",
    "with_connection_retry",
    "with_llm_retry",
    "OperationBatch",
    "OperationResult",
    "TransactionResult",
    "ZemaxLDE",
    "SurfaceType",
    "GlassCatalog",
    "ZemaxAnalysis",
    "ZemaxOptimizer",
    "MeritOperand",
    "ZemaxSystemSettings",
    "ApertureType",
    "FieldType",
]
