"""Base connector contract that every pluggable source implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class FetchResult:
    """Normalized output every connector returns, regardless of source shape."""

    source_name: str
    records: List[Dict[str, Any]]
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def record_count(self) -> int:
        return len(self.records)


class BaseConnector(ABC):
    """Every connector implements `fetch()` and returns a `FetchResult`.

    Subclasses should NOT implement their own retry loop -- wrap the
    network/IO call inside `fetch()` with `@retry_with_backoff(...)` instead,
    so every connector gets the same retry behaviour for free.
    """

    name: str

    @abstractmethod
    def fetch(self) -> FetchResult:
        """Pull data from the source and return it in a normalized shape."""
        raise NotImplementedError
