"""A small plugin registry so new connectors can be added without touching
the code that runs them -- register a class, and it becomes available by
name to the scheduler and CLI.
"""

from __future__ import annotations

from typing import Dict, Type

from .base import BaseConnector


class ConnectorRegistry:
    _connectors: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_cls: Type[BaseConnector]) -> None:
        if name in cls._connectors:
            raise ValueError(f"connector '{name}' is already registered")
        cls._connectors[name] = connector_cls

    @classmethod
    def get(cls, name: str) -> Type[BaseConnector]:
        try:
            return cls._connectors[name]
        except KeyError as exc:
            known = ", ".join(sorted(cls._connectors)) or "(none registered)"
            raise KeyError(f"no connector registered as '{name}'. Known: {known}") from exc

    @classmethod
    def known_connectors(cls):
        return sorted(cls._connectors)

    @classmethod
    def _reset_for_tests(cls) -> None:
        cls._connectors.clear()


def register_connector(name: str):
    """Class decorator: @register_connector("csv_file") class Foo(BaseConnector): ..."""

    def decorator(connector_cls: Type[BaseConnector]) -> Type[BaseConnector]:
        ConnectorRegistry.register(name, connector_cls)
        return connector_cls

    return decorator
