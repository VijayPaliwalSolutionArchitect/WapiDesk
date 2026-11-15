# WapiDesk — Running Locally

## Start

```bash
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Copy `.env.example` → `.env` (pydantic-settings auto-loads it). Full table in
`docs/env-config.md`.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `backend/data/wapidesk.db` | SQLite path |
| `WHATSAPP_VERIFY_TOKEN` | `""` | Meta verify token |
| `WHATSAPP_CLOUD_API_TOKEN` | `""` | Meta Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | Meta phone number id |
| `KNOWLEDGE_MAX_SOURCES` | `3` | Max citations |
| `QA_CONFIDENCE_THRESHOLD` | `0.4` | QA flag threshold |

## Smoke test (offline)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo","text":"hi"}'
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo","text":"what is your return policy?"}'
curl -X POST http://127.0.0.1:8000/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"channel":"web","sender":"demo","text":"STATUS ORD-1002"}'
curl http://127.0.0.1:8000/api/v1/stats
```

## Tests

```bash
python -m pytest
```

## Troubleshooting

- **Port in use** → change port or free 8000.
- **DB locked** → stop extra uvicorn workers.
- **WhatsApp webhook 403** → check `WHATSAPP_VERIFY_TOKEN` matches Meta console.
