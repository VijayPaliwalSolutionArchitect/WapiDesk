"""WapiDesk API — FastAPI application entrypoint.

Run with (from the ``backend`` directory):

    uvicorn app.main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routes import actions, channels, desk, ops
from .services import SupportAgent
from .storage import Store


def build_app(database_url: str | None = None) -> FastAPI:
    """Create the FastAPI app with a fresh runtime state.

    ``database_url`` defaults to the configured ``DATABASE_URL``; the test suite
    passes ``":memory:"`` for an isolated, throw-away database per app instance.
    """
    store = Store(database_url=database_url or settings.database_url)
    agent = SupportAgent(store, settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "WhatsApp & Web AI Support Hub — grounded knowledge answers, "
            "order/booking/complaint tools, per-customer memory and human handoff."
        ),
    )

    # Should be tightened to an allow-list in production (see docs/DEPLOYMENT.md).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Process-wide runtime state consumed by the router dependencies.
    app.state.store = store
    app.state.agent = agent

    app.include_router(channels.router)
    app.include_router(actions.router)
    app.include_router(desk.router)
    app.include_router(ops.router)

    # Minimal demo web widget for the web chat channel (FR-W1).
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir():
        app.mount("/widget", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/health", tags=["system"])
    def health() -> dict:
        """Liveness probe."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "database": "ready",
        }

    @app.get("/", include_in_schema=False)
    def index() -> HTMLResponse:
        return HTMLResponse(
            '<!doctype html><meta charset="utf-8">'
            '<h2>WapiDesk API is running.</h2>'
            '<p><a href="/docs">OpenAPI docs</a> &middot; '
            '<a href="/widget">Open the support widget</a> &middot; '
            '<a href="/health">Health</a></p>'
        )

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optional lifespan to close the SQLite connection on shutdown."""
    yield
    app.state.store.close()


app = build_app()


# Needed so the lifespan context is used when running `uvicorn app.main:app`.
app.router.lifespan_context = lifespan