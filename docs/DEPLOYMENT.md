# WapiDesk — Deployment

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Playbook deployment path: single VPS behind Caddy TLS (optionally via
Coolify), with the WhatsApp Cloud API webhook pointed at the public URL.

---

## 1. Local / dev

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 2. VPS with systemd

```ini
# /etc/systemd/system/wapidesk.service
[Unit]
Description=WapiDesk API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/WapiDesk/backend
Environment=DATABASE_URL=/var/lib/wapidesk/wapidesk.db
# Secrets below go in a systemd drop-in or /etc/wapidesk.env (chmod 600),
# NEVER in the repo:
#   WHATSAPP_VERIFY_TOKEN=…  WHATSAPP_WEBHOOK_SECRET=…
#   WHATSAPP_CLOUD_API_TOKEN=…  WHATSAPP_PHONE_NUMBER_ID=…
EnvironmentFile=-/etc/wapidesk.env
ExecStart=/opt/WapiDesk/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo apt update && sudo apt install -y python3.14 python3.14-venv git
sudo mkdir -p /opt/WapiDesk /var/lib/wapidesk
sudo git clone <repo-url> /opt/WapiDesk
cd /opt/WapiDesk
python3.14 -m venv backend/.venv
backend/.venv/bin/pip install -r requirements.txt
sudo systemctl daemon-reload && sudo systemctl enable --now wapidesk
```

## 3. TLS reverse proxy (Caddy)

```
desk.shivamitcs.com {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy auto-provisions Let's Encrypt TLS.

## 4. WhatsApp Cloud API webhook setup (Meta dashboard)

1. Callback URL: `https://desk.shivamitcs.com/api/v1/webhook/whatsapp`
2. Verify token: the same value as `WHATSAPP_VERIFY_TOKEN` on the server —
   the `GET` handshake echoes `hub.challenge` only when
   `hub.verify_token` matches.
3. Subscribe to `messages` events. Optionally set `WHATSAPP_WEBHOOK_SECRET`
   and validate `X-Hub-Signature-256` on inbound POSTs.

## 5. Docker (optional)

```dockerfile
# Dockerfile at repo root
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
WORKDIR /app/backend
ENV DATABASE_URL=/data/wapidesk.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  wapidesk:
    build: .
    ports: ["8000:8000"]
    volumes: ["./data:/data"]
    env_file: .env        # real secrets live here, git-ignored — NOT in the repo
```

## 6. Coolify (per playbook)

1. New **Docker Compose** resource pointing at the repo.
2. Domain `desk.shivamitcs.com` → automatic TLS.
3. Add env vars in the Coolify panel (or a mounted `.env`): `DATABASE_URL`,
   `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_WEBHOOK_SECRET`, `WHATSAPP_CLOUD_API_TOKEN`,
   `WHATSAPP_PHONE_NUMBER_ID`, optionally `DIFY_*`, `RAGFLOW_*`, `CHATWOOT_*`.
   Use Coolify's **secret** type for tokens.
4. Deploy; verify `https://desk.shivamitcs.com/health` → `{"status":"ok"}` and
   complete the Meta webhook verification.

## 7. Backups

```bash
sqlite3 /var/lib/wapidesk/wapidesk.db "VACUUM INTO '/backups/wapidesk-$(date +%F).db'"
```

Nightly cron + git for code. `backend/data/`, `.env` are git-ignored.

## 8. Hardening notes

- Reference build has **no auth** on desk/ops routes — put the service behind
  the reverse proxy and add an API key / Entra ID auth before exposing the desk
  publicly.
- All WhatsApp/Meta/Dify/RAGFlow/Chatwoot credentials are env-only; rotate by
  editing the platform secret store, never the repo.
- SQLite = single writer; fine at reference volumes. Swap `DATABASE_URL` to
  Postgres for multi-node.
