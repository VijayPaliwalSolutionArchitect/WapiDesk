# WapiDesk — WhatsApp Support Desk

A WhatsApp-first customer support desk: one API brain, many channels, human
handoff, and ops tooling (knowledge, CSAT, broadcasts, QA flags). Built as a
portfolio hero project — fully runnable offline with a deterministic in-app
brain, and ready to proxy to real Dify / RAGFlow / Chatwoot / WhatsApp Cloud
API when credentials are provided.

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

---

## What it does

- **WhatsApp Cloud API webhook** (`POST /api/v1/webhook/whatsapp`) with
  Meta-style verification (`GET …/whatsapp?hub.mode=hub.verify&hub.challenge=…&hub.verify_token=…`).
- **Web live-chat** (`POST /api/v1/chat`) that converges on the *same* one
  session store and the same agent brain as WhatsApp (FR-W1: one brain, many
  channels).
- **Deterministic support brain** (`services.py`): intent routing
  (order status / booking / complaint / human handoff / smalltalk) over a
  seeded knowledge base, orders, services and bookings — no external calls
  required.
- **Actions API** (`/api/v1`): order status lookup, bookings
  (create/list/cancel), complaints (create/list/get/escalate/resolve).
- **Human desk** (`/api/v1/desk`): conversation list/detail, handoff to a
  human agent, resume bot control, per-customer memory (get/forget — GDPR-style).
- **Ops API** (`/api/v1`): knowledge Q&A with sources, CSAT submit + stats,
  broadcasts, opt-out list, QA flags for low-confidence conversations.

## Architecture at a glance

```
WhatsApp Cloud API ──webhook──┐
Web chat widget ──/api/v1/chat├─► FastAPI app ─► SupportAgent (brain)
                               │      │              ├─ deterministic rules + seeded knowledge
                               │      │              └─ optional proxies: Dify / RAGFlow / Chatwoot
                               │      ▼
                               │   SQLite Store (one session store)
                               │      knowledge · orders · bookings · complaints
                               │      conversations · memory · csat · optout · broadcasts
                               └─► /api/v1/desk + /api/v1 ops for humans & dashboards
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full layered view.

## Quickstart

```bash
cd C:/Vijay-Projects/WapiDesk
python -m venv backend/.venv
source backend/.venv/Scripts/activate          # Windows git-bash
pip install -r requirements.txt                # requirements live at repo root
cd backend
uvicorn app.main:app --reload --port 8000
```

Then:

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}

curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","text":"Where is my order ORD-1001?"}'

curl http://127.0.0.1:8000/api/v1/knowledge?q=What are your opening hours?
curl http://127.0.0.1:8000/docs        # interactive Swagger UI
```

Run the tests (isolated in-memory DB):

```bash
cd backend && python -m pytest        # all API tests pass
```

## Configuration

All settings come from `backend/.env` / environment variables via
`pydantic-settings` — see [docs/env-config.md](docs/env-config.md) and
[.env.example](.env.example). **No real secrets in the repo**: WhatsApp,
Dify, RAGFlow and Chatwoot credentials are empty by default and the app runs
fully offline. Never commit real tokens.

## Docs

| Doc | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, data flow, components, schema |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Prerequisites, venv, dependencies, DB |
| [docs/RUNNING.md](docs/RUNNING.md) | Start modes, env vars, endpoints, curl walkthrough |
| [docs/API.md](docs/API.md) | Every REST endpoint with request/response examples |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | VPS, systemd, Docker, Coolify, Caddy TLS, backups, webhook URL setup |
| [docs/FEATURES.md](docs/FEATURES.md) | Implemented vs planned, mapped to code |
| [docs/TECH-STACK.md](docs/TECH-STACK.md) | Libraries, versions, rationale |
| [docs/PLAYBOOK-CROSSWALK.md](docs/PLAYBOOK-CROSSWALK.md) | Playbook requirements → implementation mapping |
| [docs/env-config.md](docs/env-config.md) | Every environment variable with defaults/examples |

## Roadmap

- ◻ Real WhatsApp send (Cloud API token) — webhook receive already works
- ◻ Dify / RAGFlow proxy for the brain when `DIFY_*` / `RAGFLOW_*` are set
- ◻ Chatwoot handoff integration (`CHATWOOT_*`)
- ◻ Auth on the desk/ops APIs
- ◻ Postgres for multi-node deployments

## Repo layout

```
WapiDesk/
├── .env.example            # all config vars, secrets as placeholders
├── requirements.txt        # fastapi, uvicorn, pydantic, pydantic-settings, pytest, httpx
├── backend/
│   ├── app/
│   │   ├── main.py         # app factory build_app(), routers, /health, static index
│   │   ├── config.py       # pydantic-settings Settings (env/.env)
│   │   ├── models.py       # Pydantic request/response models
│   │   ├── storage.py      # SQLite Store: schema, seed, CRUD
│   │   ├── services.py     # SupportAgent brain (deterministic + optional proxies)
│   │   ├── deps.py         # FastAPI dependencies (get_store, get_agent)
│   │   └── routes/         # channels.py, actions.py, desk.py, ops.py
│   └── tests/              # pytest + httpx TestClient (in-memory DB)
└── frontend/ (empty placeholder) / static index served at /
```
