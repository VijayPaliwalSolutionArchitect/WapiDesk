# WapiDesk — Features

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

✅ = implemented and tested · ◐ = partial · ◻ = planned.

## Channels — ✅
- **WhatsApp Cloud API webhook receive**: `POST /api/v1/webhook/whatsapp`
  parses Meta event payloads and returns the structured agent reply in-band.
- **Webhook verification handshake**: `GET /api/v1/webhook/whatsapp` echoes
  `hub.challenge` when `hub.verify_token` matches `WHATSAPP_VERIFY_TOKEN`.
- **Web live chat**: `POST /api/v1/chat` — same `Store` + `SupportAgent` as
  WhatsApp (FR-W1: one session store, many channels).

## Support brain — ✅ (deterministic, offline)
- Intent routing in `services.py`: `order_status`, `booking`, `complaint`,
  `handoff` ("speak to a human"), `smalltalk`, `knowledge` fallback.
- Seeded knowledge base, orders, services, bookings answer without network.
- Confidence score on every reply; below `QA_CONFIDENCE_THRESHOLD` (0.4) the
  conversation is flagged for QA review (`GET /api/v1/stats/qa-flags`).
- ◐ Optional proxies to Dify (`DIFY_AGENT_URL/KEY`) and RAGFlow
  (`RAGFLOW_URL/KEY`) when configured — offline brain remains the default.

## Actions — ✅ (`/api/v1`)
- Order status: `GET /api/v1/orders/{order_id}/status` (status + ETA + items).
- Bookings: create / list (filter by `customer_id`) / cancel — validated
  against business hours (`DEFAULT_HOURS`).
- Complaints: create / list (filter by status) / get / escalate / resolve
  (tickets `TKT-…` with full status history).

## Human desk — ✅ (`/api/v1/desk`)
- Conversation list/detail with full transcripts.
- Handoff to human (`status → handed_off`, returns `HandoffReceipt`) and
  resume bot control.
- Per-customer memory: `GET` all entries, `DELETE` one key or all
  (GDPR-style erasure).
- ◐ Real Chatwoot handoff when `CHATWOOT_*` env vars are set.

## Ops — ✅ (`/api/v1`)
- Knowledge Q&A with sources: `GET /api/v1/knowledge?q=…`, `GET /api/v1/knowledge/list`.
- CSAT: `POST /api/v1/csat` (1–5 + comment), aggregates `GET /api/v1/stats/csat`.
- Broadcasts: create/list; opted-out customers (`POST /api/v1/optout`) are
  excluded (`storage.is_opted_out`).
- QA flags: `GET /api/v1/stats/qa-flags`.

## System — ✅
- `GET /health`, static demo page at `/`, Swagger at `/docs`, ReDoc, OpenAPI.
- pydantic-settings config from env + `backend/.env`; **zero secrets in repo**.
- Tests: `backend/tests/` (pytest + httpx, in-memory DB).

## Planned — ◻
- Outbound WhatsApp sends via Cloud API (`WHATSAPP_CLOUD_API_TOKEN` +
  `WHATSAPP_PHONE_NUMBER_ID`).
- Auth on desk/ops APIs (API key or Entra ID).
- Postgres via `DATABASE_URL` for multi-node.
- Rich message templates (buttons, lists) on WhatsApp.
