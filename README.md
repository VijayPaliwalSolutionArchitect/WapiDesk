# WapiDesk — WhatsApp AI Customer-Support Agent

**WapiDesk** is a self-contained AI customer-support agent that runs on the
WhatsApp Cloud API (and a web widget) with a deterministic, offline "brain" —
so the whole agent loop is runnable and testable **without any external LLM
service or paid API**.

It implements the full playbook (Project 6): intent classification, RAG-style
grounded answers with citations, an action layer (order status, bookings,
complaint tickets), per-customer memory with a forget control, human handoff
with transcript + summary, CSAT, and broadcast opt-out.

> **Demo mode:** the deterministic in-app engine handles every message. Point
> the optional integration env vars (Dify / RAGFlow / Chatwoot / Meta) at real
> deployments to go live — the webhook still works offline with curl.

---

## What's inside

| Slice | Tech | Purpose |
|---|---|---|
| `backend/` | Python 3.10+ · FastAPI · Pydantic v2 · `pydantic-settings` · stdlib `sqlite3` · Uvicorn | REST API + deterministic agent brain (`services.py`) + storage (`storage.py`). |
| `backend/app/routes/` | `channels.py`, `actions.py`, `desk.py`, `ops.py` | WhatsApp webhook + web chat, orders/bookings/complaints, conversations/memory/handoff, knowledge/CSAT/broadcasts. |
| `backend/tests/` | pytest · httpx TestClient | API + engine tests (runs against `:memory:`). |
| `docs/` | Markdown | Architecture, API, installation, running, deployment, playbook crosswalk. |

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows git-bash (or .venv\Scripts\activate)
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open:

- Interactive API docs → <http://127.0.0.1:8000/docs>
- Health → <http://127.0.0.1:8000/api/health>

## Try it end to end (offline demo)

```bash
# Greet
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo-user","text":"hi"}'

# Grounded knowledge answer (with citations)
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo-user","text":"what is your return policy?"}'

# Order status (action)
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo-user","text":"STATUS ORD-1002"}'

# File a complaint → ticket
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo-user","text":"my order arrived damaged, I want a refund"}'

# Human handoff
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo-user","text":"I want to talk to a human agent"}'

# WhatsApp webhook (Meta envelope or plain text)
curl -X POST http://127.0.0.1:8000/api/v1/webhook/whatsapp -H 'Content-Type: application/json' \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"text":{"body":"track my order ORD-1001"}}],"contacts":[{"wa_id":"9199999"}]}}]}]}'
```

## API surface

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/chat` | Send a message → structured `AgentReply` (intent, confidence, sources, action) |
| `POST` | `/api/v1/webhook/whatsapp` | WhatsApp Cloud API inbound webhook |
| `GET` | `/api/v1/orders/{id}/status` | Order status lookup |
| `GET/POST` | `/api/v1/bookings` · `POST /api/v1/bookings/{id}/cancel` | Bookings |
| `POST` | `/api/v1/complaints` · `POST /api/v1/complaints/{id}/resolve` | Complaint tickets |
| `GET` | `/api/v1/desk/conversations/{id}` | Conversation + transcript |
| `GET/PUT/DELETE` | `/api/v1/desk/memory/{customer_id}` | Memory read / write / forget |
| `POST` | `/api/v1/desk/handoff` | Human takeover (transcript + summary) |
| `POST` | `/api/v1/knowledge/query` | Grounded RAG answer with citations |
| `POST` | `/api/v1/csat` | Submit CSAT rating |
| `POST` | `/api/v1/broadcasts` · opt-out | Broadcast + unsubscribe |
| `GET` | `/api/v1/stats` | Dashboard aggregates |
| `GET` | `/api/health` | Liveness |

Full detail in [docs/API.md](docs/API.md).

## Configuration

All settings are env vars (see `backend/app/config.py` and `docs/env-config.md`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `backend/data/wapidesk.db` | SQLite path (`:memory:` for tests) |
| `WHATSAPP_VERIFY_TOKEN` | `""` | Meta webhook verify token |
| `WHATSAPP_CLOUD_API_TOKEN` | `""` | Meta Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | Meta phone number id |
| `DIFY_AGENT_URL` / `DIFY_AGENT_KEY` | `""` | Optional external agent proxy |
| `RAGFLOW_URL` / `RAGFLOW_API_KEY` | `""` | Optional external RAG proxy |
| `CHATWOOT_URL` / tokens | `""` | Optional helpdesk proxy |
| `KNOWLEDGE_MAX_SOURCES` | `3` | Max citations per answer |
| `QA_CONFIDENCE_THRESHOLD` | `0.4` | Below this → flagged for QA |

Copy `.env.example` → `.env`.

## Repository layout

```
WapiDesk/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI factory + router wiring
│   │   ├── config.py        # pydantic-settings (env / .env)
│   │   ├── models.py        # Pydantic request/response schemas
│   │   ├── storage.py       # sqlite3 Store: schema + seed + all data access
│   │   ├── services.py      # SupportAgent — the deterministic brain
│   │   ├── seed_data.py     # Knowledge base, orders, services, memory seeds
│   │   ├── deps.py          # DI providers (store, agent)
│   │   └── routes/          # channels, actions, desk, ops
│   ├── tests/               # pytest suite
│   └── requirements.txt
├── docs/
└── .env.example
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Installation](docs/INSTALLATION.md)
- [Running Locally](docs/RUNNING.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Environment Config](docs/env-config.md)
- [Playbook Crosswalk](docs/PLAYBOOK-CROSSWALK.md)

---
*Reference implementation: deterministic brain, no paid APIs, no stored secrets.*
