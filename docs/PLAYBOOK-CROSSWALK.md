# WapiDesk — Playbook Crosswalk

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Maps each section of the WapiDesk playbook chapter
(`playbook_chapters/WapiDesk.txt`) to the actual implementation.
Status: ✅ implemented · ◐ partial · ◻ planned.

## 1. Project Snapshot

| Playbook requirement | Implementation |
|---|---|
| WhatsApp-first support desk: bot + human handoff + ops | ✅ `routes/channels.py`, `routes/desk.py`, `routes/ops.py` |
| Target: SMEs/service businesses wanting WhatsApp support without heavy tooling | ✅ README |
| One-line pitch | ✅ README tagline |
| Portfolio hero framing | ✅ README + this crosswalk |

## 2. The Demand

| Playbook point | Where addressed |
|---|---|
| Customers live on WhatsApp; businesses answer manually | ✅ README; webhook + chat channels |
| Need one brain across channels (no duplicated bots) | ✅ FR-W1: `deps.py` singletons — one `Store`, one `SupportAgent` for WhatsApp + web chat |
| Need audit, compliance, CSAT | ✅ `conversations` transcript, `optout`, `memory` erasure, `csat`, QA flags |

## 3. Architecture Layers

| Layer | Code |
|---|---|
| Channels | `routes/channels.py` — `POST/GET /api/v1/webhook/whatsapp`, `POST /api/v1/chat` |
| API | `routes/actions.py` (`/api/v1`), `routes/desk.py` (`/api/v1/desk`), `routes/ops.py` (`/api/v1`) |
| Domain brain | `services.py` `SupportAgent` — intents: order_status, booking, complaint, handoff, smalltalk, knowledge; confidence scoring; optional Dify/RAGFlow proxy |
| Persistence | `storage.py` — SQLite `Store` with 10 tables + seed |
| Config | `config.py` — pydantic-settings, env + `backend/.env` |
| Schemas | `models.py` — all request/response models |

Diagrams: [ARCHITECTURE.md](ARCHITECTURE.md).

## 4. PRD / MoSCoW

| Priority | Feature | Status |
|---|---|---|
| Must | WhatsApp webhook receive + verify handshake | ✅ `channels.py` |
| Must | Web chat on same brain/store (FR-W1) | ✅ `POST /api/v1/chat` |
| Must | Order status, bookings, complaints actions | ✅ `actions.py` |
| Must | Human handoff + resume | ✅ `desk.py` handoff/resume |
| Must | Knowledge answers with sources | ✅ `ops.py /knowledge` |
| Should | CSAT + stats | ✅ `/csat`, `/stats/csat` |
| Should | Broadcasts + opt-out | ✅ `/broadcasts`, `/optout` |
| Should | QA flags for low confidence | ✅ `/stats/qa-flags` |
| Should | Customer memory + erasure (GDPR) | ✅ `desk.py /memory` GET/DELETE |
| Could | Real outbound WhatsApp sends | ◻ webhook receive works; sends need `WHATSAPP_CLOUD_API_TOKEN` |
| Could | Dify/RAGFlow/Chatwoot live proxy | ◻ env-configured hooks in `services.py`/`config.py`, offline default |
| Won't (this phase) | Desk auth/RBAC, multi-tenant | ◻ |

## 5. Functional Requirements

| FR | Endpoint/code | Status |
|---|---|---|
| FR-W1 one session store, many channels | `deps.py` singletons shared by channels.py | ✅ |
| FR-W2 inbound webhook + verification | `POST/GET /api/v1/webhook/whatsapp` | ✅ |
| FR-W3 deterministic answers offline | `services.py` seeded knowledge + intents | ✅ |
| FR-W4 actions (orders/bookings/complaints) | `actions.py` | ✅ |
| FR-W5 handoff to human | `desk.py` handoff/resume + `HandoffReceipt` | ✅ |
| FR-W6 memory + erasure | `desk.py` memory GET/DELETE, `storage.py` memory table | ✅ |
| FR-W7 CSAT + QA flags | `ops.py` csat/stats/qa-flags | ✅ |
| FR-W8 broadcasts respecting opt-out | `ops.py` broadcasts/optout, `storage.is_opted_out` | ✅ |

Full request/response examples: [API.md](API.md).

## 6. KPIs

| KPI (playbook) | Measured via |
|---|---|
| First-response time / automation rate | `conversations` table (created_at vs first reply, status) |
| CSAT | `GET /api/v1/stats/csat` (count, average, distribution) |
| Escalation rate | complaints `status=escalated`; conversations `handed_off` |
| Quality | `GET /api/v1/stats/qa-flags` (confidence < threshold) |
| Compliance | optout list; memory erasure endpoint |

## 7. Work Breakdown

1. `config.py` + `models.py` — settings & schemas
2. `storage.py` — schema, seed, CRUD (10 tables)
3. `services.py` — SupportAgent brain
4. `routes/channels.py` → `actions.py` → `desk.py` → `ops.py`
5. `main.py` + `deps.py` — wiring, `/health`, static index
6. `backend/tests/` — pytest + httpx (in-memory DB)
7. Docs: README + this `docs/` set + `.env.example`

## 8. Deliverables

| Deliverable | Location |
|---|---|
| Runnable backend + tests | `backend/app/`, `backend/tests/` |
| API contract | `/docs`, `/openapi.json`, `docs/API.md` |
| Deployment | `docs/DEPLOYMENT.md` (systemd/Docker/Coolify/Caddy + Meta webhook setup) |
| Portfolio docs | `README.md`, `docs/PLAYBOOK-CROSSWALK.md` (this file) |

## 9. Benefits

- Customers get answers on the channel they already use (WhatsApp).
- One brain, one session store → consistent experience across channels.
- Compliance baked in: opt-out, memory erasure, transcripts, QA flags.
- Runs offline for free; flip env vars to go live with Meta/Dify/Chatwoot.

## 10. Deployment steps

[DEPLOYMENT.md](DEPLOYMENT.md): local dev → VPS+systemd → Caddy TLS → Meta
webhook verification → Docker/Coolify → backups. ✅ documented.

## 11. Portfolio angle

- Demonstrates: omnichannel design (one brain, many channels), webhook
  verification, deterministic agent logic + confidence/QA, compliance
  (opt-out, erasure), and clean API design.
- Talking points: "FR-W1: WhatsApp and web chat share one session store —
  start on WhatsApp, continue on the website, same memory."
