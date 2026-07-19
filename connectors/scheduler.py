"""A minimal interval scheduler for running a connector unattended.

This is intentionally not a cron replacement -- it's the smallest thing that
demonstrates the pattern: run a job every N seconds, keep running after a
single failure (log it, don't crash the process), and stop after a fixed
number of runs when a limit is given (used by tests and CI so the process
actually terminates).
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class IntervalScheduler:
    def __init__(self, interval_seconds: float, sleep_func: Callable[[float], None] = time.sleep):
        self.interval_seconds = interval_seconds
        self._sleep_func = sleep_func

    def run(self, job: Callable[[], None], max_runs: Optional[int] = None) -> int:
        """Run `job` every `interval_seconds`. Returns the number of runs executed.

        A single job failure is logged and swallowed so one bad run doesn't
        kill the whole scheduled process -- the next interval still fires.
        """

        runs_completed = 0
        while max_runs is None or runs_completed < max_runs:
            try:
                job()
            except Exception:  # noqa: BLE001 - a scheduler must survive job failures
                logger.exception("scheduled job raised an unhandled exception")
            runs_completed += 1
            if max_runs is not None and runs_completed >= max_runs:
                break
            self._sleep_func(self.interval_seconds)
        return runs_completed
