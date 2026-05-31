"""Tests for exponential backoff retry decorator."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from zemax_agent.api.exceptions import LLMError, ZOSConnectionError, ZemaxAgentError
from zemax_agent.api.retry import retry_on_failure, with_connection_retry, with_llm_retry


class TestRetryOnFailure:
    """测试 retry_on_failure 装饰器。"""

    @pytest.fixture(autouse=True)
    def _patch_sleep(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.sleep_calls = 0

        def fake_sleep(delay: float) -> None:
            self.sleep_calls += 1

        monkeypatch.setattr("zemax_agent.api.retry.time.sleep", fake_sleep)

    def test_success_no_retry(self) -> None:
        call_count = 0

        @retry_on_failure(max_attempts=3)
        def succeed() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        result = succeed()
        assert result == 42
        assert call_count == 1
        assert self.sleep_calls == 0

    def test_retry_on_retryable_exception(self) -> None:
        call_count = 0

        @retry_on_failure(max_attempts=3, retryable_exceptions=(ValueError,))
        def flaky() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("flaky error")
            return 99

        result = flaky()
        assert result == 99
        assert call_count == 3
        assert self.sleep_calls == 2

    def test_non_retryable_raises_immediately(self) -> None:
        call_count = 0

        @retry_on_failure(
            max_attempts=3,
            retryable_exceptions=(ValueError,),
            non_retryable_exceptions=(TypeError,),
        )
        def fail_fast() -> int:
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            fail_fast()

        assert call_count == 1
        assert self.sleep_calls == 0

    def test_raises_after_max_attempts(self) -> None:
        @retry_on_failure(max_attempts=3, retryable_exceptions=(RuntimeError,))
        def always_fails() -> int:
            raise RuntimeError("always fail")

        with pytest.raises(RuntimeError, match="always fail"):
            always_fails()

        assert self.sleep_calls == 2

    def test_on_retry_callback(self) -> None:
        callback_log: list[tuple[Exception, int]] = []

        def on_retry(exception: Exception, attempt: int) -> None:
            callback_log.append((exception, attempt))

        call_count = 0

        @retry_on_failure(
            max_attempts=3,
            retryable_exceptions=(ValueError,),
            on_retry=on_retry,
        )
        def flaky_with_callback() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("oops")
            return 7

        result = flaky_with_callback()
        assert result == 7
        assert len(callback_log) == 2
        assert callback_log[0][1] == 1
        assert callback_log[1][1] == 2

    def test_jitter_affects_delay(self, monkeypatch: pytest.MonkeyPatch) -> None:
        delays: list[float] = []

        def capture_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("zemax_agent.api.retry.time.sleep", capture_sleep)

        call_count = 0

        @retry_on_failure(
            max_attempts=3,
            base_delay=1.0,
            backoff_factor=2.0,
            jitter=True,
            retryable_exceptions=(ValueError,),
        )
        def flaky_jitter() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("jitter test")
            return 10

        flaky_jitter()
        assert len(delays) == 2
        assert all(d > 0 for d in delays)

    def test_max_delay_cap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        delays: list[float] = []

        def capture_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("zemax_agent.api.retry.time.sleep", capture_sleep)

        call_count = 0

        @retry_on_failure(
            max_attempts=5,
            base_delay=50.0,
            max_delay=1.0,
            backoff_factor=2.0,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )
        def flaky_capped() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                raise ValueError("capped")
            return 20

        flaky_capped()
        assert len(delays) == 4
        assert all(d <= 1.0 for d in delays)

    def test_no_jitter_exact_delays(self, monkeypatch: pytest.MonkeyPatch) -> None:
        delays: list[float] = []

        def capture_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("zemax_agent.api.retry.time.sleep", capture_sleep)

        call_count = 0

        @retry_on_failure(
            max_attempts=4,
            base_delay=1.0,
            backoff_factor=2.0,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )
        def flaky_exact() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ValueError("exact")
            return 30

        flaky_exact()
        assert len(delays) == 3
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0

    def test_default_retryable_is_exception(self) -> None:
        call_count = 0

        @retry_on_failure(max_attempts=3)
        def flaky_default() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("default retryable")
            return 55

        result = flaky_default()
        assert result == 55
        assert call_count == 2

    def test_logger_warning_on_retry(self, caplog: pytest.LogCaptureFixture) -> None:
        call_count = 0

        @retry_on_failure(max_attempts=3, retryable_exceptions=(ValueError,))
        def flaky_log() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("log test")
            return 66

        with caplog.at_level(logging.WARNING, logger="zemax_agent.api.retry"):
            flaky_log()

        assert any("失败" in record.message for record in caplog.records)


class TestPresetDecorators:
    """测试预设重试装饰器。"""

    @pytest.fixture(autouse=True)
    def _patch_sleep(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("zemax_agent.api.retry.time.sleep", lambda d: None)

    def test_with_connection_retry_as_decorator(self) -> None:
        call_count = 0

        @with_connection_retry(max_attempts=3)
        def connect() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ZOSConnectionError("failed")
            return 1

        result = connect()
        assert result == 1
        assert call_count == 3

    def test_with_connection_retry_non_zemax_error_not_retried(self) -> None:
        call_count = 0

        @with_connection_retry(max_attempts=3)
        def connect_value_error() -> int:
            nonlocal call_count
            call_count += 1
            raise ValueError("not a connection error")

        with pytest.raises(ValueError):
            connect_value_error()
        assert call_count == 1

    def test_with_connection_retry_as_callable(self) -> None:
        call_count = 0

        def connect() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ZOSConnectionError("fail")
            return 2

        decorated = with_connection_retry(connect, max_attempts=2)
        result = decorated()
        assert result == 2
        assert call_count == 2

    def test_with_llm_retry_as_decorator(self) -> None:
        call_count = 0

        @with_llm_retry(max_attempts=3)
        def llm_call() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise LLMError("llm fail")
            return 3

        result = llm_call()
        assert result == 3
        assert call_count == 3

    def test_with_llm_retry_connection_error(self) -> None:
        call_count = 0

        @with_llm_retry(max_attempts=3)
        def llm_conn() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("connection error")
            return 4

        result = llm_conn()
        assert result == 4
        assert call_count == 3

    def test_with_llm_retry_timeout_error(self) -> None:
        call_count = 0

        @with_llm_retry(max_attempts=3)
        def llm_timeout() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timeout")
            return 5

        result = llm_timeout()
        assert result == 5
        assert call_count == 3

    def test_with_connection_retry_non_zemax_not_retried(self) -> None:
        call_count = 0

        @with_connection_retry(max_attempts=3)
        def conn_other() -> int:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("not zemax")

        with pytest.raises(RuntimeError, match="not zemax"):
            conn_other()
        assert call_count == 1
