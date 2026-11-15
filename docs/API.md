# WapiDesk — API Reference

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

- **Base URL:** `http://127.0.0.1:8000`
- **Interactive docs:** `/docs` (Swagger), `/redoc`, schema at `/openapi.json`
- **Auth:** none in the reference build (all desk/ops routes are open locally)
- **Errors:** FastAPI standard — `{"detail": "..."}` for 404/422 etc.

Routers: `channels.py` (no prefix), `actions.py` (`/api/v1`),
`desk.py` (`/api/v1/desk`), `ops.py` (`/api/v1`).

---

## System

### `GET /health`
```bash
curl http://127.0.0.1:8000/health
```
```json
{"status": "ok"}
```

### `GET /`
Static demo page (`index.html`), served outside the API schema.

---

## Channels

### `POST /api/v1/chat` — web live-chat (same brain as WhatsApp)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","text":"Where is my order ORD-1001?"}'
```
```json
{
  "conversation_id": "conv_…",
  "reply": "Your order ORD-1001 is out for delivery, ETA 2026-11-16.",
  "intent": "order_status",
  "confidence": 0.95,
  "action": {"type": "order_status", "order_id": "ORD-1001", "status": "out_for_delivery"},
  "sources": []
}
```
`MessageIn`: `{customer_id, text, channel?}` → `AgentReply`:
`{conversation_id, reply, intent, confidence, action, sources}`.

### `POST /api/v1/webhook/whatsapp` — WhatsApp Cloud API webhook (receive)
Accepts the Meta event payload; extracts the customer's text and returns the
structured agent reply in-band (demo mode — no Meta app needed to test):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/webhook/whatsapp \
  -H 'Content-Type: application/json' \
  -d '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"from":"919876543210","text":{"body":"book a haircut tomorrow 10am"}}]}}]}]}'
```

### `GET /api/v1/webhook/whatsapp` — Meta verification handshake
```bash
curl "http://127.0.0.1:8000/api/v1/webhook/whatsapp?hub.mode=hub.verify&hub.challenge=CHALLENGE&hub.verify_token=your-verify-token"
# -> {"hub.challenge": "CHALLENGE"}   (only when hub.verify_token matches WHATSAPP_VERIFY_TOKEN)
```

---

## Actions — prefix `/api/v1` (`routes/actions.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/orders/{order_id}/status` | Order status + ETA → `OrderStatus` (404 if unknown) |
| `GET` | `/api/v1/bookings?customer_id=` | List bookings (optionally per customer) |
| `POST` | `/api/v1/bookings` | Create booking `{customer_id, service, date, time?}` → `BookingOut` |
| `POST` | `/api/v1/bookings/{booking_id}/cancel` | Cancel → `BookingOut` |
| `POST` | `/api/v1/complaints` | Open ticket `{customer_id, channel?, category, message}` → `ComplaintOut` |
| `GET` | `/api/v1/complaints?status=` | List tickets (optional status filter) |
| `GET` | `/api/v1/complaints/{ticket_id}` | Ticket detail |
| `POST` | `/api/v1/complaints/{ticket_id}/escalate` | Status → `escalated` |
| `POST` | `/api/v1/complaints/{ticket_id}/resolve` | Body `{resolution}` → status `resolved` |

```bash
curl -X POST http://127.0.0.1:8000/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","service":"Haircut","date":"2026-11-16","time":"10:00"}'
# -> {"booking_id":"BK-…","customer_id":"C-100","service":"Haircut","date":"2026-11-16","time":"10:00","status":"confirmed","hours":"09:00-18:00"}

curl -X POST http://127.0.0.1:8000/api/v1/complaints \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","category":"refund","message":"I was charged twice"}'
```

---

## Human desk — prefix `/api/v1/desk` (`routes/desk.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/desk/conversations?status=` | List conversations (`open`, `handed_off`, …) |
| `GET` | `/api/v1/desk/conversations/{conversation_id}` | Full transcript + status |
| `POST` | `/api/v1/desk/conversations/{conversation_id}/handoff` | Hand to human → `HandoffReceipt {conversation_id, status:"handed_off", queued_at, note}` |
| `POST` | `/api/v1/desk/conversations/{conversation_id}/resume` | Bot resumes control → `ConversationOut` |
| `GET` | `/api/v1/desk/memory/{customer_id}` | Per-customer memory → `MemoryOut {customer_id, entries:[{key,value,updated_at}]}` |
| `DELETE` | `/api/v1/desk/memory/{customer_id}?key=` | Forget one key, or all (`key` omitted) → `{"deleted": n}` (GDPR-style erasure) |

```bash
curl -X POST http://127.0.0.1:8000/api/v1/desk/conversations/conv_123/handoff
curl http://127.0.0.1:8000/api/v1/desk/memory/C-100
curl -X DELETE "http://127.0.0.1:8000/api/v1/desk/memory/C-100?key=preferred_language"
```

---

## Ops — prefix `/api/v1` (`routes/ops.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/knowledge?q=…` | Knowledge-base answer with sources → `KnowledgeAnswer {answer, sources:[…], confidence}` |
| `GET` | `/api/v1/knowledge/list` | List all KB entries |
| `POST` | `/api/v1/csat` | Submit rating `{conversation_id, rating (1-5), comment?}` → `CsatOut` |
| `GET` | `/api/v1/stats/csat` | CSAT aggregates → `CsatStats {count, average_rating, distribution}` |
| `POST` | `/api/v1/broadcasts` | Create broadcast `{title, body, audience}` → `BroadcastOut` |
| `GET` | `/api/v1/broadcasts` | List broadcasts |
| `POST` | `/api/v1/optout` | `{customer_id}` — mark customer opted out of broadcasts |
| `GET` | `/api/v1/stats/qa-flags` | Conversations flagged for QA review (confidence < `QA_CONFIDENCE_THRESHOLD`) → `[QaFlag]` |

```bash
curl "http://127.0.0.1:8000/api/v1/knowledge?q=What%20are%20your%20opening%20hours%3F"
curl -X POST http://127.0.0.1:8000/api/v1/csat \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":"conv_123","rating":5,"comment":"Resolved fast"}'
curl http://127.0.0.1:8000/api/v1/stats/csat
curl http://127.0.0.1:8000/api/v1/stats/qa-flags
```

## Notes

- Opted-out customers (`/api/v1/optout`) are excluded from broadcasts and the
  agent will not initiate proactive messages to them.
- Low-confidence replies (`confidence < QA_CONFIDENCE_THRESHOLD`, default 0.4)
  are recorded as QA flags instead of silently answering.
