# resilient-connector-framework

A reusable framework for pulling data from multiple external sources -- files, APIs, anything with a `fetch()` -- with retry-with-backoff, scheduling, and error handling built in once, at the framework level, instead of copy-pasted into every connector. This is the pattern behind the "50+ source connectors" and "reduced new source integration time from days to hours" work described in my portfolio, rebuilt from scratch as a small open-source demo (client code itself isn't public).

## Setup

```
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```
python main.py
python -m pytest tests/ -v
```

Run tests as `python -m pytest`, not bare `pytest` -- see the real snag below for why that distinction actually matters here.

`main.py` registers the demo connectors and runs a `FlakyDemoConnector` that's configured to fail twice before succeeding, so you can see the retry/backoff logging fire in real time on every run.

## What's actually happening under the hood

```
connectors/base.py       -- BaseConnector contract: every source implements fetch() -> FetchResult
connectors/retry.py      -- retry_with_backoff(): the decorator every connector's fetch() wraps
connectors/registry.py   -- ConnectorRegistry: name -> class lookup, so adding a source doesn't
                             mean touching the code that runs existing ones
connectors/scheduler.py  -- IntervalScheduler: runs a job on a fixed interval, survives a single
                             job failure without crashing the whole process
connectors/sources.py    -- example connectors: CSVFileConnector, RestApiConnector, and
                             FlakyDemoConnector (used to test retry behaviour deterministically)
```

A new source is a class with one method (`fetch`), decorated with `@retry_with_backoff(...)`, registered under a name. Nothing else in the framework needs to change.

## Design notes

**Why inject the HTTP client into `RestApiConnector` instead of importing `requests` directly?** So the connector's retry/error-handling logic can be tested with a fake client that returns canned responses -- no real network call, no flaky external dependency in CI, and the test can deterministically force a 500 response to prove the retry path actually fires.

**Why does the scheduler swallow job exceptions instead of letting them propagate?** Because the entire point of an unattended scheduled job is that one bad run (a timeout, a malformed record) shouldn't take down the process that's supposed to run again in an hour. The exception is logged, not silently dropped -- `test_scheduler.py` proves the process keeps running after a failure, and a real deployment would ship those logs to monitoring rather than just stdout.

**Why a class-based registry instead of a plain dict some module exposes?** Mainly so registering the same name twice is an explicit, loud `ValueError` instead of one connector silently overwriting another -- a mistake that's easy to make once a framework has more than a handful of sources.

## A real snag while building this

The first CI run failed with `ModuleNotFoundError: No module named 'connectors'` on every test file, even though the code ran fine locally. The workflow called `pytest tests/ -v` directly, and plain `pytest` doesn't add the current working directory to `sys.path` the way `python -m pytest` does -- so the `connectors` package next to `tests/` simply wasn't importable in CI's process. Fixed by changing both the CI step and the documented usage to `python -m pytest tests/ -v`. A small distinction, but it's the difference between "works on my machine" and "works in CI."

## Where this would change for production

- **Scheduling:** `IntervalScheduler` is a simple loop; a real deployment would run connectors as Airflow tasks or a managed cron (this mirrors the pattern in [airflow-etl-demo](https://github.com/aayushi-jha2018/airflow-etl-demo)), with the interval and retry policy configured per-DAG instead of per-process.
- **Sources:** `CSVFileConnector` and `RestApiConnector` are intentionally simple; production sources would add auth, pagination, and rate-limit handling on top of the same `BaseConnector`/`retry_with_backoff` contract.
- **Observability:** the scheduler logs to Python's `logging` module; production would ship those logs/metrics to CloudWatch or similar so a silently-failing connector gets alerted on, not just logged.

## Layout

```
connectors/
  __init__.py
  base.py          -- BaseConnector, FetchResult
  retry.py         -- retry_with_backoff, RetryExhaustedError
  registry.py      -- ConnectorRegistry, register_connector
  scheduler.py     -- IntervalScheduler
  sources.py       -- CSVFileConnector, RestApiConnector, FlakyDemoConnector
tests/
  test_retry.py
  test_registry.py
  test_scheduler.py
  test_sources.py
main.py
requirements.txt
.github/workflows/ci.yml
```

MIT license.
