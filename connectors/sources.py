"""Example pluggable connectors: CSV file, REST API, and a deliberately-flaky
in-memory source used to exercise the retry logic in tests without needing a
real flaky endpoint.
"""

from __future__ import annotations

import csv
import random
from typing import Any, Dict, List, Optional

from .base import BaseConnector, FetchResult
from .retry import retry_with_backoff


class CSVFileConnector(BaseConnector):
    """Reads records from a local CSV file."""

    name = "csv_file"

    def __init__(self, path: str):
        self.path = path

    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def fetch(self) -> FetchResult:
        with open(self.path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            records: List[Dict[str, Any]] = list(reader)
        return FetchResult(source_name=self.name, records=records)


class RestApiConnector(BaseConnector):
    """Fetches JSON records from a REST API using an injected HTTP client.

    The HTTP client is injected (rather than importing `requests` directly)
    so tests can pass in a fake client with no network calls at all.
    """

    name = "rest_api"

    def __init__(self, url: str, http_get):
        self.url = url
        self._http_get = http_get

    @retry_with_backoff(max_attempts=4, base_delay=0.2)
    def fetch(self) -> FetchResult:
        response = self._http_get(self.url)
        if response.get("status") != 200:
            raise ConnectionError(f"non-200 response: {response.get('status')}")
        return FetchResult(source_name=self.name, records=response.get("data", []))


class FlakyDemoConnector(BaseConnector):
    """An in-memory source that fails a configurable number of times before
    succeeding. This exists purely to demonstrate and test the retry/backoff
    behaviour deterministically, without depending on a real unreliable
    service being down at the right moment.
    """

    name = "flaky_demo"

    def __init__(
        self,
        fail_times: int,
        records: Optional[List[Dict[str, Any]]] = None,
        seed: Optional[int] = None,
    ):
        self.fail_times = fail_times
        self._records = records or [{"id": 1, "value": "ok"}]
        self._attempts_made = 0
        self._rng = random.Random(seed)

    @retry_with_backoff(max_attempts=5, base_delay=0.05)
    def fetch(self) -> FetchResult:
        self._attempts_made += 1
        if self._attempts_made <= self.fail_times:
            raise TimeoutError(f"simulated timeout on attempt {self._attempts_made}")
        return FetchResult(source_name=self.name, records=self._records)
