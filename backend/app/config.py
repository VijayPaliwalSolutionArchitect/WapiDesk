"""Application settings loaded from environment / .env via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the WapiDesk backend.

    Everything can be overridden by environment variables (see ``.env``). The
    defaults keep the service runnable out-of-the-box with only the seeded
    in-app data engine.
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---
    app_name: str = "WapiDesk API"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Persistence ---
    # Absolute or relative path to the SQLite database file. Use ":memory:" to
    # keep everything in memory (used by the test suite).
    database_url: str = str(BACKEND_DIR / "data" / "wapidesk.db")

    # --- WhatsApp Cloud API (Meta) ---
    # These are intentionally unset by default. In local/demo mode the webhook
    # endpoint still works — it treats the inbound payload as customer text and
    # returns the agent reply in-band — so no Meta app is required to run.
    whatsapp_verify_token: str = ""
    whatsapp_webhook_secret: str = ""
    whatsapp_cloud_api_token: str = ""
    whatsapp_phone_number_id: str = ""

    # --- External integrations (optional, off by default) ---
    # When unset, the deterministic in-app brain is used so the service works
    # offline and is testable. Point these at a real deployment of Dify /
    # RAGFlow / Chatwoot to proxy to the production brain and desk.
    dify_agent_url: str = ""
    dify_agent_key: str = ""
    ragflow_url: str = ""
    ragflow_api_key: str = ""
    chatwoot_url: str = ""
    chatwoot_account_id: str = ""
    chatwoot_bot_token: str = ""

    # --- Behavior ---
    knowledge_max_sources: int = 3
    # Confidence below which a conversation is flagged for human QA review.
    qa_confidence_threshold: float = 0.4
    default_hours: str = "09:00-18:00"


# Module-level singleton so routers import the same resolved settings.
settings = Settings()