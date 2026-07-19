"""Tests for the example connectors, including the CSV connector against a
real temp file and the REST connector against a fake injected HTTP client."""

from __future__ import annotations

import pytest

from connectors.sources import CSVFileConnector, RestApiConnector


def test_csv_connector_reads_rows(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("id,name\n1,Alpha\n2,Beta\n", encoding="utf-8")

    result = CSVFileConnector(str(csv_file)).fetch()

    assert result.source_name == "csv_file"
    assert result.record_count == 2
    assert result.records[0]["name"] == "Alpha"


def test_csv_connector_missing_file_raises_after_retries():
    connector = CSVFileConnector("does/not/exist.csv")
    with pytest.raises(Exception):
        connector.fetch()


def test_rest_api_connector_success():
    def fake_get(url):
        return {"status": 200, "data": [{"id": 1}, {"id": 2}]}

    result = RestApiConnector("https://example.invalid/api", http_get=fake_get).fetch()

    assert result.record_count == 2


def test_rest_api_connector_retries_on_non_200_then_raises():
    call_count = {"n": 0}

    def flaky_get(url):
        call_count["n"] += 1
        return {"status": 500, "data": []}

    connector = RestApiConnector("https://example.invalid/api", http_get=flaky_get)
    with pytest.raises(Exception):
        connector.fetch()

    assert call_count["n"] == 4  # max_attempts configured on RestApiConnector.fetch
