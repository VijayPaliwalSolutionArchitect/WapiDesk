"""Shared pytest fixtures for the WapiDesk backend tests.

Each test gets an isolated, in-memory app so tests are deterministic and need no
database file. Requires httpx + pytest (both in requirements.txt).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the app package importable when running pytest from the backend dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import build_app  # noqa: E402


@pytest.fixture()
def client():
    """FastAPI TestClient backed by a fresh in-memory SQLite database."""
    app = build_app(database_url=":memory:")
    with TestClient(app) as c:
        yield c