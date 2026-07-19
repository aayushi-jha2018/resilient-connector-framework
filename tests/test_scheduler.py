"""Proves the scheduler runs the expected number of times and survives a job
that raises, instead of crashing the whole process on the first failure."""

from __future__ import annotations

from connectors.scheduler import IntervalScheduler


def test_runs_exact_number_of_times_with_max_runs():
    calls = []
    scheduler = IntervalScheduler(interval_seconds=0, sleep_func=lambda _: None)

    completed = scheduler.run(lambda: calls.append(1), max_runs=5)

    assert completed == 5
    assert len(calls) == 5


def test_survives_a_failing_job_and_keeps_scheduling():
    calls = []

    def flaky_job():
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("simulated failure on the 2nd run")

    scheduler = IntervalScheduler(interval_seconds=0, sleep_func=lambda _: None)
    completed = scheduler.run(flaky_job, max_runs=4)

    # All 4 runs still execute even though run #2 raised.
    assert completed == 4
    assert len(calls) == 4
