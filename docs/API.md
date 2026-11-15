# WapiDesk — API Reference

Base URL: `http://127.0.0.1:8000`. Interactive docs at `/docs`.

## Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |

## Channels (FR-W1)

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/chat` | `MessageIn {channel, sender, text, conversation_id?}` | Send a message → `AgentReply` |
| `POST` | `/api/v1/webhook/whatsapp` | Meta Cloud API envelope (or plain text in demo mode) | WhatsApp inbound webhook |
| `GET` | `/api/v1/webhook/whatsapp` | `hub.mode` / `hub.verify_token` query | Meta webhook verification |

`AgentReply` = `{conversation_id, reply, intent, confidence, sources[], memory_used[], action_taken?, handed_to_human}`

## Actions (FR-W3 / FR-W4)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/orders/{order_id}/status` | Order status (404 if unknown) |
| `GET` | `/api/v1/bookings?customer_id=…` | List bookings |
| `POST` | `/api/v1/bookings` | Create booking `{customer_id, service, date, time}` |
| `POST` | `/api/v1/bookings/{id}/cancel` | Cancel a booking |
| `POST` | `/api/v1/complaints` | Register complaint → ticket with SLA |
| `GET` | `/api/v1/complaints/{id}` | Ticket detail |
| `POST` | `/api/v1/complaints/{id}/resolve` | Resolve ticket `{notes}` |

## Desk (FR-W5 / FR-W6)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/desk/conversations/{id}` | Conversation + full transcript |
| `POST` | `/api/v1/desk/handoff` | Human takeover → transcript + summary receipt |
| `POST` | `/api/v1/desk/resume` | Hand control back to the AI |
| `GET` | `/api/v1/desk/memory/{customer_id}` | Read customer memory |
| `PUT` | `/api/v1/desk/memory/{customer_id}` | Write memory key/value |
| `DELETE` | `/api/v1/desk/memory/{customer_id}` | Forget all memory (privacy control) |

## Ops (FR-W2 / FR-W7 / FR-W8)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/knowledge/query` | Grounded answer `{question}` → `{answer, sources[], confidence, flagged_for_qa}` |
| `POST` | `/api/v1/csat` | Submit rating `{conversation_id, score 1-5}` |
| `GET` | `/api/v1/csat` | CSAT aggregates |
| `POST` | `/api/v1/broadcasts` | Send broadcast (respects opt-outs) |
| `POST` | `/api/v1/opt-out` | Unsubscribe a sender |
| `GET` | `/api/v1/stats` | Dashboard: conversations, tickets, CSAT, handoffs |

## Intents

`greeting · order_status · booking · complaint · human · broadcast_optout · csat · thanks · unknown`

## Errors

Standard FastAPI shape: `{"detail": "..."}`; validation → `422` with field detail.
