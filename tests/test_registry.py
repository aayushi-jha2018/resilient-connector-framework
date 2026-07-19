"""Proves the registry rejects duplicate names and gives a helpful error for
unknown connectors, instead of a bare KeyError."""

from __future__ import annotations

import pytest

from connectors.base import BaseConnector, FetchResult
from connectors.registry import ConnectorRegistry, register_connector


class _DummyConnector(BaseConnector):
    name = "dummy"

    def fetch(self) -> FetchResult:
        return FetchResult(source_name=self.name, records=[])


@pytest.fixture(autouse=True)
def _clean_registry():
    ConnectorRegistry._reset_for_tests()
    yield
    ConnectorRegistry._reset_for_tests()


def test_register_and_get_roundtrip():
    register_connector("dummy")(_DummyConnector)
    assert ConnectorRegistry.get("dummy") is _DummyConnector
    assert ConnectorRegistry.known_connectors() == ["dummy"]


def test_duplicate_registration_raises():
    register_connector("dummy")(_DummyConnector)
    with pytest.raises(ValueError):
        register_connector("dummy")(_DummyConnector)


def test_unknown_connector_raises_helpful_error():
    register_connector("dummy")(_DummyConnector)
    with pytest.raises(KeyError) as exc_info:
        ConnectorRegistry.get("does_not_exist")
    assert "dummy" in str(exc_info.value)
