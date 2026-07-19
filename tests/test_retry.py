"""Proves the retry decorator actually retries, actually backs off, and
actually gives up after max_attempts -- not just that it exists."""

from __future__ import annotations

import pytest

from connectors.retry import RetryExhaustedError, retry_with_backoff


def test_succeeds_without_retry_when_first_call_works():
    calls = []

    @retry_with_backoff(max_attempts=3, base_delay=0, sleep_func=lambda _: None)
    def always_ok():
        calls.append(1)
        return "ok"

    assert always_ok() == "ok"
    assert len(calls) == 1


def test_retries_then_succeeds():
    calls = []

    @retry_with_backoff(max_attempts=3, base_delay=0, sleep_func=lambda _: None)
    def fails_twice_then_ok():
        calls.append(1)
        if len(calls) < 3:
            raise TimeoutError("simulated")
        return "ok"

    assert fails_twice_then_ok() == "ok"
    assert len(calls) == 3


def test_gives_up_after_max_attempts():
    calls = []

    @retry_with_backoff(max_attempts=3, base_delay=0, sleep_func=lambda _: None)
    def always_fails():
        calls.append(1)
        raise TimeoutError("simulated, always fails")

    with pytest.raises(RetryExhaustedError) as exc_info:
        always_fails()

    assert len(calls) == 3
    assert exc_info.value.attempts == 3


def test_backoff_delay_grows_between_attempts():
    sleeps = []

    @retry_with_backoff(
        max_attempts=4,
        base_delay=1.0,
        backoff_factor=2.0,
        sleep_func=lambda d: sleeps.append(d),
    )
    def always_fails():
        raise ValueError("simulated")

    with pytest.raises(RetryExhaustedError):
        always_fails()

    # 3 sleeps between 4 attempts, doubling each time.
    assert sleeps == [1.0, 2.0, 4.0]


def test_only_catches_configured_exception_types():
    @retry_with_backoff(max_attempts=3, base_delay=0, exceptions=(TimeoutError,), sleep_func=lambda _: None)
    def raises_value_error():
        raise ValueError("not a timeout, should not be retried")

    with pytest.raises(ValueError):
        raises_value_error()
