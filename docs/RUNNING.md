# WapiDesk — Running Locally

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

## 1. Start the server

From the repo root with the venv active:

```bash
cd backend
uvicorn app.main:app --reload --port 8000

# Production-style
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The lifespan hook creates/seeds `backend/data/wapidesk.db` on boot.

## 2. URLs

| URL | What |
|---|---|
| <http://127.0.0.1:8000/> | Static demo page |
| <http://127.0.0.1:8000/health> | `{"status":"ok"}` |
| <http://127.0.0.1:8000/docs> / `/redoc` / `/openapi.json` | Swagger / ReDoc / schema |

## 3. Environment variables

Loaded by pydantic-settings from `backend/.env` (copy `.env.example` from the
repo root). Environment variables override the file. Full table with examples:
[env-config.md](env-config.md). Summary:

| Variable | Default | Effect |
|---|---|---|
| `DATABASE_URL` | `backend/data/wapidesk.db` | SQLite file (`:memory:` supported) |
| `APP_NAME` / `APP_VERSION` | `WapiDesk API` / `1.0.0` | OpenAPI metadata |
| `DEBUG` | `false` | Debug mode |
| `WHATSAPP_VERIFY_TOKEN` | `""` | Meta webhook verification token |
| `WHATSAPP_WEBHOOK_SECRET` | `""` | X-Hub-Signature-256 validation (when set) |
| `WHATSAPP_CLOUD_API_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID` | `""` | Outbound sends (future) |
| `DIFY_AGENT_URL` / `DIFY_AGENT_KEY` | `""` | Proxy brain to Dify |
| `RAGFLOW_URL` / `RAGFLOW_API_KEY` | `""` | Proxy knowledge to RAGFlow |
| `CHATWOOT_URL` / `CHATWOOT_ACCOUNT_ID` / `CHATWOOT_BOT_TOKEN` | `""` | Real human-desk handoff |
| `KNOWLEDGE_MAX_SOURCES` | `3` | Max KB sources returned per answer |
| `QA_CONFIDENCE_THRESHOLD` | `0.4` | Below this, conversations are QA-flagged |
| `DEFAULT_HOURS` | `09:00-18:00` | Business hours shown in replies/bookings |

## 4. Endpoint walkthrough (curl)

```bash
B=http://127.0.0.1:8000

# Health + chat
curl $B/health
curl -X POST $B/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","text":"Where is my order ORD-1001?"}'
curl -X POST $B/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","text":"I want to speak to a human"}'

# WhatsApp webhook (demo payload) + verification handshake
curl -X POST $B/api/v1/webhook/whatsapp -H 'Content-Type: application/json' -d '{...meta event...}'
curl "$B/api/v1/webhook/whatsapp?hub.mode=hub.verify&hub.challenge=abc&hub.verify_token=your-verify-token"

# Actions
curl $B/api/v1/orders/ORD-1001/status
curl -X POST $B/api/v1/bookings -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","service":"Haircut","date":"2026-11-16","time":"10:00"}'
curl "$B/api/v1/bookings?customer_id=C-100"
curl -X POST $B/api/v1/complaints -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","category":"refund","message":"charged twice"}'
curl -X POST $B/api/v1/complaints/TKT-1/escalate

# Desk
curl "$B/api/v1/desk/conversations?status=open"
curl -X POST $B/api/v1/desk/conversations/<conv_id>/handoff
curl -X POST $B/api/v1/desk/conversations/<conv_id>/resume
curl $B/api/v1/desk/memory/C-100
curl -X DELETE "$B/api/v1/desk/memory/C-100"

# Ops
curl "$B/api/v1/knowledge?q=opening%20hours"
curl $B/api/v1/knowledge/list
curl -X POST $B/api/v1/csat -H 'Content-Type: application/json' \
  -d '{"conversation_id":"<conv_id>","rating":5}'
curl $B/api/v1/stats/csat
curl -X POST $B/api/v1/broadcasts -H 'Content-Type: application/json' \
  -d '{"title":"Holiday hours","body":"We are closed on Sunday","audience":"all"}'
curl $B/api/v1/broadcasts
curl -X POST $B/api/v1/optout -H 'Content-Type: application/json' -d '{"customer_id":"C-100"}'
curl $B/api/v1/stats/qa-flags
```

Full schemas: [API.md](API.md).

## 5. Tests

```bash
cd backend
python -m pytest          # test_api.py uses an in-memory DB via conftest.py
```

## 6. Stopping

`Ctrl+C`. SQLite commits per write; no shutdown hook needed.
