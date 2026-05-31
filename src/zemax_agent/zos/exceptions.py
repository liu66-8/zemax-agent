from __future__ import annotations

from typing import Any


class ZOSError(Exception):
    pass


class ZOSConnectionError(ZOSError):
    pass


class ZOSTimeoutError(ZOSError):
    pass


class ZOSCOMError(ZOSError):
    pass


class ZOSParameterError(ZOSError):
    pass


class ZOSNotConnectedError(ZOSError):
    pass


class ZOSOperationError(ZOSError):
    def __init__(self, message: str = "", operation: str = "", details: dict[str, Any] | None = None):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class ZOSOptimizationError(ZOSError):
    pass


class ZOSAnalysisError(ZOSError):
    pass


def is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (ZOSConnectionError, ZOSTimeoutError, ZOSCOMError))


RETRYABLE_TYPES = (ZOSConnectionError, ZOSTimeoutError, ZOSCOMError)
