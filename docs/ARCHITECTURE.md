# WapiDesk — Architecture

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

## Layered view

```
┌────────────────────────────────────────────────────────────────────┐
│  Channels (entry points)                                           │
│  • WhatsApp Cloud API webhook  POST/GET /api/v1/webhook/whatsapp  │
│  • Web live-chat widget        POST /api/v1/chat                   │
│  • Static demo page            GET /                               │
├────────────────────────────────────────────────────────────────────┤
│  API layer (FastAPI routers, app/routes/)                          │
│  • channels.py  — webhook ingest + chat, returns AgentReply        │
│  • actions.py   — /api/v1 orders, bookings, complaints             │
│  • desk.py      — /api/v1/desk conversations, handoff, memory      │
│  • ops.py       — /api/v1 knowledge, csat, broadcasts, optout,     │
│                   stats                                            │
├────────────────────────────────────────────────────────────────────┤
│  Domain layer                                                      │
│  • services.py  — SupportAgent: intent routing + reply building    │
│                   (deterministic brain; optional Dify/RAGFlow      │
│                   proxy when configured)                           │
│  • models.py    — Pydantic v2 request/response schemas             │
├────────────────────────────────────────────────────────────────────┤
│  Persistence                                                       │
│  • storage.py   — SQLite Store (one session store for all channels)│
│  • config.py    — pydantic-settings (env / backend/.env)          │
└────────────────────────────────────────────────────────────────────┘
```

## Request flow (a WhatsApp message)

```mermaid
sequenceDiagram
    participant WA as WhatsApp Cloud API
    participant API as FastAPI (routes/channels.py)
    participant AG as SupportAgent (services.py)
    participant DB as SQLite Store (storage.py)
    WA->>API: POST /api/v1/webhook/whatsapp (event payload)
    API->>DB: get/create conversation + append user message
    API->>AG: reply(customer_id, text, channel)
    AG->>DB: knowledge lookup, orders/bookings/services, memory, optout check
    AG-->>API: AgentReply {text, intent, confidence, action, sources}
    API->>DB: append agent message; flag for QA if confidence < threshold
    API-->>WA: JSONResponse with the structured reply
```

## Components table

| Component | File | Responsibility |
|---|---|---|
| App factory | `backend/app/main.py` | `build_app()` wires store + agent via `deps.py`, mounts routers, serves `/health`, `/` (static `index.html`), `/docs` |
| Settings | `backend/app/config.py` | `Settings(BaseSettings)` — env vars + `backend/.env`; DB path, WhatsApp/Dify/RAGFlow/Chatwoot credentials (all empty by default), thresholds |
| Schemas | `backend/app/models.py` | `MessageIn`, `AgentReply`, `BookingCreate/Out`, `ComplaintCreate/Resolve/Out`, `ConversationOut`, `HandoffReceipt`, `MemoryOut`, `KnowledgeAnswer`, `CsatIn/Out/Stats`, `BroadcastCreate/Out`, `OptOutBody`, `QaFlag`, … |
| Store | `backend/app/storage.py` | SQLite schema + seed + CRUD: `knowledge`, `orders`, `services`, `bookings`, `complaints`, `conversations`, `memory`, `optout`, `csat`, `broadcast` |
| Brain | `backend/app/services.py` | `SupportAgent.reply()` — intent detection (order/booking/complaint/handoff/smalltalk/knowledge), confidence score, action payloads, QA flagging, optional external proxies |
| Dependencies | `backend/app/deps.py` | `get_store`, `get_agent` — singletons per app instance |
| Routers | `backend/app/routes/*.py` | channels / actions / desk / ops (see API.md) |

## SQLite schema (storage.py)

```
knowledge(id, question, answer, tags, source)
orders(order_id, customer_id, status, eta, items_json)
services(id, name, duration_min, price)
bookings(booking_id, customer_id, service, date, time, status, hours)
complaints(ticket_id, customer_id, channel, category, message, status, resolution, created_at, updated_at)
conversations(conversation_id, customer_id, channel, status, created_at, updated_at, messages_json, last_intent, confidence)
memory(customer_id, key, value, updated_at)
optout(customer_id, created_at)
csat(id, conversation_id, rating, comment, created_at)
broadcast(id, title, body, audience, created_at, sent_count)
```

## Key design decisions

1. **One session store, many channels** (playbook FR-W1): WhatsApp webhook and
   web chat share the same `Store` and `SupportAgent`, so a conversation started
   on WhatsApp continues seamlessly on web chat and vice versa.
2. **Deterministic offline brain**: with no external credentials set, intent
   routing + seeded knowledge answer everything — reproducible tests, no API
   keys, no network. Setting `DIFY_*`/`RAGFLOW_*` switches the brain to proxy a
   real LLM/RAG; `CHATWOOT_*` wires handoff to a real desk.
3. **SQLite single file** (`backend/data/wapidesk.db` by default): zero-ops,
   trivial backups, swappable for Postgres later by changing `database_url`.
4. **Compliance built in**: `optout` table (customers who opted out of
   broadcasts — checked before any send), `DELETE /api/v1/desk/memory/{id}` for
   data erasure, QA flags for low-confidence replies.
5. **No secrets in code**: every credential is an env var with an empty
   default; `.env` is git-ignored.
