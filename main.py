"""CLI entry point: runs a demo connector once and prints a summary.

Usage:
    python main.py
"""

from __future__ import annotations

import logging

from connectors.registry import ConnectorRegistry, register_connector
from connectors.sources import CSVFileConnector, FlakyDemoConnector

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Register the demo connectors under names the CLI/tests can look up.
try:
    register_connector("csv_file")(CSVFileConnector)
except ValueError:
    pass  # already registered (e.g. re-running in the same interpreter/tests)

try:
    register_connector("flaky_demo")(FlakyDemoConnector)
except ValueError:
    pass


def run_all() -> None:
    print(f"Registered connectors: {ConnectorRegistry.known_connectors()}")

    demo = FlakyDemoConnector(fail_times=2, records=[{"id": 1, "value": "sample"}], seed=42)
    result = demo.fetch()
    print(
        f"[{result.source_name}] fetched {result.record_count} record(s) "
        f"at {result.fetched_at.isoformat()}"
    )


if __name__ == "__main__":
    run_all()
