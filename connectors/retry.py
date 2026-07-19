"""Retry-with-backoff decorator used by every connector in this framework.

Real external sources fail intermittently: a timeout, a 500 from an API, a
locked file. The point of this decorator is to make "retry a few times with
increasing delay, then give up loudly" the default behaviour for any fetch
function, instead of something each connector has to reimplement.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when a function still fails after all retry attempts."""

    def __init__(self, func_name: str, attempts: int, last_error: Exception):
        self.func_name = func_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"{func_name} failed after {attempts} attempt(s); "
            f"last error: {last_error!r}"
        )


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    sleep_func: Callable[[float], None] = time.sleep,
):
    """Retry the wrapped function on failure, with exponential backoff.

    Attempt 1 runs immediately. If it raises one of `exceptions`, the
    decorator waits `base_delay`, then `base_delay * backoff_factor`, and so
    on, up to `max_attempts` total attempts. If every attempt fails, it
    raises `RetryExhaustedError` wrapping the last exception, rather than
    silently swallowing the failure.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_error: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: BLE001 - intentional broad catch
                    last_error = exc
                    logger.warning(
                        "%s attempt %d/%d failed: %r",
                        func.__name__,
                        attempt,
                        max_attempts,
                        exc,
                    )
                    if attempt == max_attempts:
                        break
                    sleep_func(delay)
                    delay *= backoff_factor
            assert last_error is not None
            raise RetryExhaustedError(func.__name__, max_attempts, last_error)

        return wrapper

    return decorator
