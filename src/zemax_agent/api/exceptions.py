"""Zemax Agent 异常类型层次体系。"""

from __future__ import annotations


class ZemaxAgentError(Exception):
    """Zemax Agent 系统基础异常"""

    pass


class ZOSConnectionError(ZemaxAgentError):
    """ZOS-API 连接相关异常（连接断开、超时、初始化失败）"""

    pass


class ZOSOperationError(ZemaxAgentError):
    """ZOS-API 操作执行异常（参数错误、操作不支持等）"""

    pass


class ZOSAnalysisError(ZemaxAgentError):
    """光学分析执行异常"""

    pass


class ZOSOptimizationError(ZemaxAgentError):
    """优化过程异常"""

    pass


class ValidationError(ZemaxAgentError):
    """参数验证异常"""

    pass


class PhysicsViolationError(ValidationError):
    """物理学规律违反异常"""

    pass


class KnowledgeConstraintError(ValidationError):
    """知识库约束违反异常"""

    pass


class ToolExecutionError(ZemaxAgentError):
    """工具函数执行异常"""

    pass


class LLMError(ZemaxAgentError):
    """大模型交互异常"""

    pass
