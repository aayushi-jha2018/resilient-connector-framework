"""Resilient connector framework: pluggable data-source connectors with retry, scheduling, and error handling."""

from .registry import ConnectorRegistry, register_connector
from .retry import retry_with_backoff
from .base import BaseConnector

__all__ = [
    "ConnectorRegistry",
    "register_connector",
    "retry_with_backoff",
    "BaseConnector",
]
