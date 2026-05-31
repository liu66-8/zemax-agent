"""Tests for batch operation transaction manager."""

from __future__ import annotations

import pytest

from zemax_agent.api.transaction import OperationBatch, OperationResult, TransactionResult


class DummyConnection:
    def __init__(self) -> None:
        self.side_effects: list[Exception] = []


class TestOperationBatchBasic:
    """测试 begin/commit 正常流程。"""

    def test_begin_commit_successful(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        results_store: list = []
        batch.add_operation(lambda: results_store.append(1))
        batch.add_operation(lambda: results_store.append(2))
        batch.add_operation(lambda: results_store.append(3))

        assert batch.is_active is True
        result = batch.commit()

        assert result.success is True
        assert result.committed is True
        assert result.rolled_back is False
        assert len(result.results) == 3
        assert all(r.success for r in result.results)
        assert results_store == [1, 2, 3]
        assert batch.is_active is False

    def test_begin_commit_single_operation(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        batch.add_operation(lambda: 42)
        result = batch.commit()

        assert result.success is True
        assert result.committed is True
        assert result.results[0].data == 42

    def test_operation_result_stores_data(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        batch.add_operation(lambda: {"key": "value"})
        result = batch.commit()

        assert result.results[0].data == {"key": "value"}


class TestOperationBatchRollback:
    """测试操作失败时自动回滚。"""

    def test_failure_triggers_rollback(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        success_values: list[int] = []
        batch.add_operation(lambda: success_values.append(1))
        batch.add_operation(lambda: (_ for _ in ()).throw(ValueError("op2 failed")))

        result = batch.commit()

        assert result.success is False
        assert result.rolled_back is True
        assert result.committed is False
        assert "op2 failed" in result.error_message
        assert len(result.results) == 2
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert isinstance(result.results[1].error, ValueError)
        assert success_values == [1]
        assert batch.is_active is False

    def test_rollback_handlers_are_called(self) -> None:
        conn = DummyConnection()
        rollback_log: list[str] = []
        batch = OperationBatch(conn)
        batch.begin()

        batch.add_operation(lambda: "op1", rollback=lambda: rollback_log.append("rb1"))
        batch.add_operation(lambda: "op2", rollback=lambda: rollback_log.append("rb2"))
        batch.add_operation(lambda: (_ for _ in ()).throw(RuntimeError("op3 fail")))

        result = batch.commit()

        assert result.success is False
        assert rollback_log == ["rb2", "rb1"]

    def test_only_executed_operations_rollback(self) -> None:
        conn = DummyConnection()
        rollback_log: list[str] = []
        batch = OperationBatch(conn)
        batch.begin()

        batch.add_operation(lambda: "op1", rollback=lambda: rollback_log.append("rb1"))
        batch.add_operation(lambda: (_ for _ in ()).throw(ValueError("fail")), rollback=lambda: rollback_log.append("rb2"))
        batch.add_operation(lambda: "never_run", rollback=lambda: rollback_log.append("rb3"))

        batch.commit()
        assert rollback_log == ["rb1"]

    def test_manual_rollback(self) -> None:
        conn = DummyConnection()
        rollback_log: list[str] = []
        batch = OperationBatch(conn)
        batch.begin()

        batch.add_operation(lambda: "op1", rollback=lambda: rollback_log.append("rb1"))
        batch.add_operation(lambda: "op2", rollback=lambda: rollback_log.append("rb2"))

        batch.rollback()

        assert rollback_log == ["rb2", "rb1"]
        assert batch.is_active is False

    def test_rollback_on_inactive_does_nothing(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.rollback()


class TestOperationBatchContextManager:
    """测试上下文管理器自动 commit/rollback。"""

    def test_context_manager_auto_commit(self) -> None:
        conn = DummyConnection()
        results_store: list[int] = []

        with OperationBatch(conn) as batch:
            batch.add_operation(lambda: results_store.append(10))
            batch.add_operation(lambda: results_store.append(20))

        assert results_store == [10, 20]
        assert batch.is_active is False

    def test_context_manager_auto_rollback_on_exception(self) -> None:
        conn = DummyConnection()
        rollback_log: list[str] = []

        with pytest.raises(ValueError, match="inner error"):
            with OperationBatch(conn) as batch:
                batch.add_operation(lambda: "ok", rollback=lambda: rollback_log.append("rb_ok"))
                raise ValueError("inner error")

        assert rollback_log == ["rb_ok"]
        assert batch.is_active is False


class TestOperationBatchErrors:
    """测试错误处理场景。"""

    def test_add_operation_without_begin_raises(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)

        with pytest.raises(RuntimeError, match="事务未开始"):
            batch.add_operation(lambda: 1)

    def test_commit_without_begin_raises(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)

        with pytest.raises(RuntimeError, match="事务未开始"):
            batch.commit()

    def test_begin_twice_raises(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        with pytest.raises(RuntimeError, match="事务已在进行中"):
            batch.begin()

        batch.commit()

    def test_rollback_handler_exception_is_warned_not_raised(self) -> None:
        conn = DummyConnection()
        batch = OperationBatch(conn)
        batch.begin()

        def bad_rollback() -> None:
            raise RuntimeError("rollback also failed")

        batch.add_operation(lambda: "op", rollback=bad_rollback)

        batch.rollback()
        assert batch.is_active is False


class TestOperationBatchDataClasses:
    """测试数据类默认值。"""

    def test_operation_result_defaults(self) -> None:
        result = OperationResult(success=True)
        assert result.data is None
        assert result.error is None

    def test_transaction_result_defaults(self) -> None:
        result = TransactionResult(success=False)
        assert result.results == []
        assert result.committed is False
        assert result.rolled_back is False
        assert result.error_message == ""

    def test_transaction_result_with_results(self) -> None:
        op_results = [OperationResult(success=True, data=42)]
        result = TransactionResult(success=True, results=op_results)
        assert len(result.results) == 1
