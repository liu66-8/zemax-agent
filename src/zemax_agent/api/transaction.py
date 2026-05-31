"""批量操作事务管理器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperationResult:
    """单个操作的结果。"""

    success: bool
    data: Any = None
    error: Optional[Exception] = None


@dataclass
class TransactionResult:
    """事务执行结果。"""

    success: bool
    results: List[OperationResult] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False
    error_message: str = ""


class OperationBatch:
    """批量操作事务管理器。

    支持 begin/commit/rollback 语义，
    在执行多个相关光学操作时保证操作原子性和可回滚性。
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._operations: List[Callable[[], Any]] = []
        self._rollback_handlers: List[Callable[[], None]] = []
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def begin(self) -> None:
        """开始事务。"""
        if self._active:
            raise RuntimeError("事务已在进行中")
        self._operations.clear()
        self._rollback_handlers.clear()
        self._active = True
        logger.debug("事务开始")

    def add_operation(
        self,
        operation: Callable[[], Any],
        rollback: Optional[Callable[[], None]] = None,
    ) -> None:
        """添加一个操作到事务中。

        Args:
            operation: 要执行的操作函数。
            rollback: 回滚函数（撤销该操作）。
        """
        if not self._active:
            raise RuntimeError("事务未开始，请先调用 begin()")
        self._operations.append(operation)
        if rollback:
            self._rollback_handlers.append(rollback)
        else:
            self._rollback_handlers.append(lambda: None)

    def commit(self) -> TransactionResult:
        """提交事务：依次执行所有操作。"""
        if not self._active:
            raise RuntimeError("事务未开始")

        results: List[OperationResult] = []
        executed_count = 0

        try:
            for i, operation in enumerate(self._operations):
                try:
                    data = operation()
                    results.append(OperationResult(success=True, data=data))
                    executed_count += 1
                except Exception as e:
                    logger.error("操作 %d 执行失败: %s", i, e)
                    results.append(OperationResult(success=False, error=e))
                    self._rollback(executed_count)
                    return TransactionResult(
                        success=False,
                        results=results,
                        rolled_back=True,
                        error_message=f"操作 {i} 失败，已回滚 {executed_count} 个操作: {e}",
                    )

            self._active = False
            logger.debug("事务提交成功，共执行 %d 个操作", executed_count)
            return TransactionResult(success=True, results=results, committed=True)
        finally:
            self._operations.clear()
            self._rollback_handlers.clear()
            self._active = False

    def rollback(self) -> None:
        """手动回滚事务。"""
        if not self._active:
            return
        executed_count = len(self._operations)
        self._rollback(executed_count)
        self._active = False
        self._operations.clear()
        self._rollback_handlers.clear()

    def _rollback(self, count: int) -> None:
        """执行回滚（倒序）。"""
        for i in range(min(count, len(self._rollback_handlers)) - 1, -1, -1):
            try:
                self._rollback_handlers[i]()
            except Exception as e:
                logger.warning("回滚操作 %d 失败: %s", i, e)

    def __enter__(self) -> OperationBatch:
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False
