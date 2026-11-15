# WapiDesk — Environment Configuration

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Settings are loaded by `backend/app/config.py` using **pydantic-settings**:
process environment variables first, then `backend/.env` (copy the repo-root
`.env.example` there). Variable names are case-insensitive.

**Secrets rule:** every credential below defaults to an empty string and the
app runs fully offline. Never commit real tokens — keep them in `.env`
(git-ignored) or your platform's secret store, and use placeholders
(`your-…-here`) in docs and tickets.

## Core

| Variable | Default | Description | Example |
|---|---|---|---|
| `APP_NAME` | `WapiDesk API` | OpenAPI title | `WapiDesk API` |
| `APP_VERSION` | `1.0.0` | OpenAPI version | `1.0.0` |
| `DEBUG` | `false` | Debug mode | `true` |

## Persistence

| Variable | Default | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | `backend/data/wapidesk.db` | SQLite path; `:memory:` for ephemeral (tests use this) | `/var/lib/wapidesk/wapidesk.db` |

## WhatsApp Cloud API (Meta)

| Variable | Default | Description | Example |
|---|---|---|---|
| `WHATSAPP_VERIFY_TOKEN` | `""` | Token Meta sends as `hub.verify_token` in the GET handshake | `your-verify-token-here` |
| `WHATSAPP_WEBHOOK_SECRET` | `""` | App secret for `X-Hub-Signature-256` validation | `your-app-secret-here` |
| `WHATSAPP_CLOUD_API_TOKEN` | `""` | Cloud API access token for outbound sends | `your-cloud-api-token-here` |
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | Phone number ID used when sending | `123456789012345` |

## Optional external brain / desk (off = deterministic in-app brain)

| Variable | Default | Description | Example |
|---|---|---|---|
| `DIFY_AGENT_URL` | `""` | Dify agent endpoint to proxy chat to | `https://api.dify.ai/v1/chat-messages` |
| `DIFY_AGENT_KEY` | `""` | Dify API key | `your-dify-key-here` |
| `RAGFLOW_URL` | `""` | RAGFlow base URL for knowledge answers | `https://ragflow.example.com` |
| `RAGFLOW_API_KEY` | `""` | RAGFlow API key | `your-ragflow-key-here` |
| `CHATWOOT_URL` | `""` | Chatwoot instance URL for real handoff | `https://app.chatwoot.com` |
| `CHATWOOT_ACCOUNT_ID` | `""` | Chatwoot account ID | `12345` |
| `CHATWOOT_BOT_TOKEN` | `""` | Chatwoot bot token | `your-chatwoot-token-here` |

## Behavior

| Variable | Default | Description | Example |
|---|---|---|---|
| `KNOWLEDGE_MAX_SOURCES` | `3` | Max KB sources attached to an answer | `5` |
| `QA_CONFIDENCE_THRESHOLD` | `0.4` | Replies below this confidence are QA-flagged (`GET /api/v1/stats/qa-flags`) | `0.5` |
| `DEFAULT_HOURS` | `09:00-18:00` | Business hours surfaced in replies and bookings | `09:00-21:00` |

## `.env` example (backend/.env)

```ini
APP_NAME=WapiDesk API
DEBUG=false
DATABASE_URL=./data/wapidesk.db

WHATSAPP_VERIFY_TOKEN=your-verify-token-here
WHATSAPP_WEBHOOK_SECRET=your-app-secret-here
WHATSAPP_CLOUD_API_TOKEN=your-cloud-api-token-here
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id-here

DIFY_AGENT_URL=
DIFY_AGENT_KEY=
RAGFLOW_URL=
RAGFLOW_API_KEY=
CHATWOOT_URL=
CHATWOOT_ACCOUNT_ID=
CHATWOOT_BOT_TOKEN=

KNOWLEDGE_MAX_SOURCES=3
QA_CONFIDENCE_THRESHOLD=0.4
DEFAULT_HOURS=09:00-18:00
```
