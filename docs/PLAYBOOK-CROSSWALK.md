# WapiDesk — Playbook Crosswalk (Project 6)

Maps every playbook requirement (FR-Wx) to the code that satisfies it.

| Playbook FR | Requirement | Where it lives |
|---|---|---|
| FR-W1 | WhatsApp Cloud API + web widget, one session store | `routes/channels.py` (webhook + `/api/v1/chat`); `storage.Store` conversations |
| FR-W2 | Grounded knowledge answers with source citations + confidence | `services.retrieve()`, `services._answer_knowledge()`, `routes/ops.py` `/api/v1/knowledge/query`; `models.Source` |
| FR-W3 | Action tools: order status + bookings | `services._answer_order/_answer_booking`, `routes/actions.py` |
| FR-W4 | Complaint tickets with SLA + status | `services._answer_complaint`, `storage.create_complaint`, `routes/actions.py` |
| FR-W5 | Per-customer memory + privacy/forget control | `storage` memory table, `routes/desk.py` memory CRUD + DELETE |
| FR-W6 | Human handoff with transcript + summary, explicit resume | `services._handoff`, `routes/desk.py` handoff/resume |
| FR-W7 | CSAT + QA flags + dashboards | `routes/ops.py` csat/stats; `QA_CONFIDENCE_THRESHOLD` flagging |
| FR-W8 | Broadcast with opt-out | `routes/ops.py` broadcasts/opt-out; `storage.opt_out` |
| — | Deterministic offline brain (no paid LLM) | `services.SupportAgent` + `score_intent` |
| — | Latency target: median first response < 4s | Single-process SQLite + in-memory brain; smoke 50 concurrent chats at deploy |

## Acceptance checks (playbook §6.5)

1. Live demo number + web widget → stranger completes an action via `/api/v1/chat`
2. Grounded KB per vertical → cited answers on seeded FAQs (`/api/v1/knowledge/query`)
3. Action layer demo → order + booking + complaint ticket visible end-to-end
4. Human handoff demo → takeover shows transcript + summary (`/api/v1/desk/handoff`)
5. Memory demo → returning-customer recognition + forget (`/api/v1/desk/memory`)
6. CSAT + QA dashboard → `/api/v1/stats` + `/api/v1/csat`
7. Broadcast with opt-out → `/api/v1/broadcasts` respects opt-outs
