# WapiDesk — Architecture

## System overview

WapiDesk is a **channel-agnostic AI support agent**. One deterministic brain
(`SupportAgent`) serves both WhatsApp Cloud API and a web widget, backed by a
single SQLite store.

```
WhatsApp Cloud API ──┐
                     ├─▶ routes/channels.py ─▶ SupportAgent ─▶ SQLite Store
Web widget ──────────┘         │                    │
                               ▼                    ▼
                        routes/actions.py     knowledge / orders /
                        routes/desk.py         bookings / complaints /
                        routes/ops.py          memory / conversations
```

## The brain (`services.py` → `SupportAgent.handle`)

One message in → structured reply out:

1. Resolve/create the conversation session (one store, many channels).
2. If already handed off → tell the customer to say RESUME.
3. `score_intent(text)` → (intent, confidence). Deterministic keyword +
   explicit-phrase classifier; an `ORD-####` id forces `order_status`.
4. `_dispatch()` routes the intent:
   - `greeting` / `thanks` → canned polite reply
   - `order_status` → lookup + write `last_order` memory
   - `booking` → parse `BOOK <svc> on <date> at <time>` or show availability
   - `complaint` → create ticket + SLA + write `open_ticket` memory
   - `human` → handoff (transcript + summary) → status `handed_off`
   - `broadcast_optout` → opt out of promos
   - `csat` → prompt for rating
   - default → **RAG**: `retrieve()` over the seeded knowledge base, answer with
     citations + confidence; low confidence → flagged for QA
5. Append the agent reply to the transcript; return `AgentReply`.

## Retrieval (RAG-style, deterministic)

`retrieve(query, docs, max_sources)` ranks knowledge docs by token overlap with
the query — body overlap counts 1, title overlap counts 0.5 — and returns the
top-N `(similarity, doc)`. `confidence_from_retrieval` = max similarity. Below
`QA_CONFIDENCE_THRESHOLD` the answer is `flagged_for_qa`.

## Persistence (`storage.py` → `Store`)

Stdlib `sqlite3`, schema created idempotently on boot, seeded from
`seed_data.py` (knowledge base, orders, services, memory, opt-outs):

| Table | Purpose |
|---|---|
| `knowledge` | RAG corpus (id, category, title, body) |
| `orders` | Order status lookups |
| `services` | Bookable services |
| `bookings` | Appointments with cancel support |
| `complaints` | Tickets with category, priority, SLA timestamp |
| `conversations` | Per-channel sessions: messages JSON, status, handoff summary |
| `memory` | Per-customer key/value (with forget control) |
| `opt_outs` | Broadcast opt-out list |
| `csat` | Ratings |

## Modules

| File | Responsibility |
|---|---|
| `app/main.py` | App factory, router wiring, health |
| `app/config.py` | `pydantic-settings` — env + `.env` |
| `app/models.py` | Pydantic I/O schemas |
| `app/storage.py` | `Store`: schema, seed, all data access |
| `app/services.py` | `SupportAgent` — intent, retrieval, dispatch |
| `app/seed_data.py` | Seeded knowledge / orders / services / memory |
| `app/deps.py` | DI providers |
| `app/routes/channels.py` | WhatsApp webhook + web chat |
| `app/routes/actions.py` | Orders, bookings, complaints |
| `app/routes/desk.py` | Conversations, memory, handoff |
| `app/routes/ops.py` | Knowledge query, CSAT, broadcasts, stats |

## Design decisions

- **Deterministic brain, zero paid APIs** — runs offline, tests are stable.
- **One session store, many channels** — same conversation whether WhatsApp or web.
- **Explicit intents win** — full-phrase overrides and `ORD-####` regex beat keywords.
- **Grounded answers always carry citations** (FR-W2).
- **Human handoff carries full context** — transcript + summary, explicit RESUME.
- **Privacy control** — per-customer memory has a forget/delete endpoint.
