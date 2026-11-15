# WapiDesk — Tech Stack

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Derived from `requirements.txt` (repo root) and the code under `backend/app/`.

## Runtime

| Technology | Constraint | Purpose | Why chosen |
|---|---|---|---|
| Python | ≥ 3.11 (cp314 wheels) | Runtime | Modern stdlib, `sqlite3`, type hints |
| FastAPI | ≥ 0.115, < 1.0 | API framework, routers, OpenAPI | Async, automatic docs, dependency injection (`deps.py`) |
| Uvicorn `[standard]` | ≥ 0.34 | ASGI server | `uvloop`/`httptools` extras |
| Pydantic | ≥ 2.11, < 3.0 | v2 models in `models.py` | Validation + schema generation |
| pydantic-settings | ≥ 2.7 | `Settings` in `config.py` | env + `.env` loading without extra deps |
| SQLite (stdlib) | — | Persistence in `storage.py` | Zero-ops single file; swappable via `DATABASE_URL` |

## Dev / test

| Technology | Constraint | Purpose |
|---|---|---|
| pytest | ≥ 8.3 | Test runner (`backend/tests/`) |
| httpx | ≥ 0.28 | `TestClient` for API tests with in-memory DB |

## Integrations (optional, env-configured, all off by default)

| Integration | Env vars | Role |
|---|---|---|
| WhatsApp Cloud API (Meta) | `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_WEBHOOK_SECRET`, `WHATSAPP_CLOUD_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | Webhook verify + receive (+ send when token set) |
| Dify | `DIFY_AGENT_URL`, `DIFY_AGENT_KEY` | External agent brain proxy |
| RAGFlow | `RAGFLOW_URL`, `RAGFLOW_API_KEY` | External knowledge base proxy |
| Chatwoot | `CHATWOOT_URL`, `CHATWOOT_ACCOUNT_ID`, `CHATWOOT_BOT_TOKEN` | Real human desk handoff |

## Data model (SQLite, `storage.py`)

`knowledge` · `orders` · `services` · `bookings` · `complaints` ·
`conversations` · `memory` · `optout` · `csat` · `broadcast`

## Architecture choices

| Decision | Rationale |
|---|---|
| One `Store` + one `SupportAgent` singleton (`deps.py`) | FR-W1: identical behavior across WhatsApp and web chat |
| Deterministic brain by default | Offline-runnable, reproducible tests, no API keys needed |
| pydantic-settings | Standard FastAPI-ecosystem config; `.env` optional |
| Raw `sqlite3` (no ORM) | Small surface, full control over schema/seed, easy Postgres swap later |
| No auth in reference build | Nothing secret to protect; production notes in DEPLOYMENT.md §8 |

## Not used (deliberately)

No ORM, no Celery/scheduler, no python-dotenv (pydantic-settings covers it),
no frontend build step (static demo page only), no Docker requirement for dev.
