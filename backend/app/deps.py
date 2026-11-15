"""FastAPI dependencies: shared store + agent instances."""

from __future__ import annotations

from starlette.requests import Request

from .services import SupportAgent
from .storage import Store


def get_store(request: Request) -> Store:
    """Resolve the process-wide Store from the app state (see main.py)."""
    return request.app.state.store


def get_agent(request: Request) -> SupportAgent:
    """Resolve the process-wide SupportAgent from the app state."""
    return request.app.state.agent