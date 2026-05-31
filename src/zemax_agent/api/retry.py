"""指数退避重试装饰器。"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (),
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable:
    """指数退避重试装饰器。

    Args:
        max_attempts: 最大尝试次数（含首次）。
        base_delay: 基础延迟秒数。
        max_delay: 最大延迟秒数。
        backoff_factor: 退避因子。
        jitter: 是否添加随机抖动。
        retryable_exceptions: 可重试的异常类型。
        non_retryable_exceptions: 不可重试的异常类型（优先于 retryable_exceptions）。
        on_retry: 重试时的回调函数 (exception, attempt_number)。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    logger.error(
                        "操作 '%s' 遇到不可重试异常: %s", func.__name__, e
                    )
                    raise
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(
                            base_delay * (backoff_factor ** (attempt - 1)), max_delay
                        )
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        logger.warning(
                            "操作 '%s' 失败 (尝试 %d/%d): %s. %.1f秒后重试...",
                            func.__name__,
                            attempt,
                            max_attempts,
                            e,
                            delay,
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        time.sleep(delay)
                    else:
                        logger.error(
                            "操作 '%s' 最终失败，已尝试 %d 次: %s",
                            func.__name__,
                            max_attempts,
                            e,
                        )
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def with_connection_retry(
    func: Callable | None = None,
    *,
    max_attempts: int = 3,
) -> Callable:
    """ZOS-API 连接操作的标准重试配置。"""

    from .exceptions import ZOSConnectionError

    decorator = retry_on_failure(
        max_attempts=max_attempts,
        base_delay=2.0,
        max_delay=30.0,
        retryable_exceptions=(ZOSConnectionError,),
        jitter=True,
    )
    if func is None:
        return decorator
    return decorator(func)


def with_llm_retry(
    func: Callable | None = None,
    *,
    max_attempts: int = 3,
) -> Callable:
    """LLM API 调用的标准重试配置。"""

    from .exceptions import LLMError

    decorator = retry_on_failure(
        max_attempts=max_attempts,
        base_delay=1.0,
        max_delay=15.0,
        retryable_exceptions=(LLMError, TimeoutError, ConnectionError),
        jitter=True,
    )
    if func is None:
        return decorator
    return decorator(func)
