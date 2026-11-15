# WapiDesk — Installation

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

## 1. Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | ≥ 3.11 (wheels target cp314) | `python --version` |
| pip | bundled | `python -m pip --version` |
| Git | any | `git --version` |

No external services are required: the default brain is deterministic and
offline, and SQLite is in the stdlib. WhatsApp / Dify / RAGFlow / Chatwoot
integrations are optional and configured via env vars only.

## 2. Get the code

```bash
cd C:/Vijay-Projects/WapiDesk        # project root
```

## 3. Create the virtual environment (inside `backend/`)

```bash
python -m venv backend/.venv
source backend/.venv/Scripts/activate     # Windows git-bash
# backend\.venv\Scripts\activate          # Windows cmd.exe
# source backend/.venv/bin/activate        # macOS / Linux
```

`backend/.venv/`, `__pycache__/`, `*.db`, `.env`, `backend/data/` are
git-ignored.

## 4. Install dependencies

The requirements file lives at the **repo root**:

```bash
pip install -r requirements.txt
```

| Package | Constraint | Purpose |
|---|---|---|
| `fastapi` | ≥ 0.115, < 1.0 | API framework + OpenAPI |
| `uvicorn[standard]` | ≥ 0.34 | ASGI server |
| `pydantic` | ≥ 2.11, < 3.0 | v2 models (`models.py`) |
| `pydantic-settings` | ≥ 2.7 | `Settings` loading from env / `backend/.env` (`config.py`) |
| `pytest` | ≥ 8.3 | tests |
| `httpx` | ≥ 0.28 | `TestClient` |

## 5. Configure environment (optional)

```bash
cp backend/.env.example backend/.env   # or copy from repo root .env.example
```

`config.py` uses pydantic-settings with `env_file = backend/.env`; process
environment variables override the file. All credentials default to empty
strings — the app runs fully offline. See [env-config.md](env-config.md).

**Never commit real tokens.** `.env` is git-ignored; use placeholders in docs.

## 6. Database initialization (automatic)

`main.py`'s lifespan handler creates the SQLite schema
(`CREATE TABLE IF NOT EXISTS …` for `knowledge`, `orders`, `services`,
`bookings`, `complaints`, `conversations`, `memory`, `optout`, `csat`,
`broadcast`) and seeds demo data (KB entries, orders, services) on first boot.

- Default DB file: `backend/data/wapidesk.db` (dir auto-created).
- Override with `DATABASE_URL` (e.g. `DATABASE_URL=:memory:` for ephemeral,
  or a Postgres URL in a future version).
- Reset: delete `backend/data/wapidesk.db` and restart.

## 7. Verify the install

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
curl http://127.0.0.1:8000/health
# -> {"status": "ok"}

curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100","text":"hi"}'

python -m pytest        # from backend/ — API tests against an in-memory DB
```

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: fastapi` | venv not active | `source backend/.venv/Scripts/activate` |
| Port 8000 busy | another process | `--port 8001` or `PORT`-style override via env if set |
| Webhook verify returns 403 | `hub.verify_token` ≠ `WHATSAPP_VERIFY_TOKEN` | set both to the same value in `backend/.env` |
| Old data after schema change | stale DB | delete `backend/data/wapidesk.db`, restart |
| Tests fail | run from `backend/` | `cd backend && python -m pytest` (conftest uses in-memory DB) |

Next: [RUNNING.md](RUNNING.md).
