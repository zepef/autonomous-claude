"""
Honeypot Module

Fake MCP server for detecting and engaging malicious AI agents.

Components:
- server: Flask-based honeypot with classifier integration
- FakeDataGenerator: Creates convincing fake responses

Usage:
    # Start honeypot server
    python -m src.honeypot.server --port 5000

    # Or programmatically
    from src.honeypot import HoneypotServer
    server = HoneypotServer(port=5000)
    server.run()
"""

from .server import (
    HoneypotServer,
    HoneypotSession,
    FakeDataGenerator,
    create_app
)

__all__ = [
    'HoneypotServer',
    'HoneypotSession',
    'FakeDataGenerator',
    'create_app'
]
