# WapiDesk — Deployment

## Local dev

```bash
uvicorn app.main:app --reload --port 8000
```

## Production VPS (per playbook §6.7)

1. Register the Meta app + WhatsApp business number; submit business
   verification early (gates the demo number).
2. Deploy the FastAPI service on the shared VPS behind **Caddy**:

   ```
   wapi.shivamitcs.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```

3. Point the Meta webhook callback at `https://wapi.shivamitcs.com/api/v1/webhook/whatsapp`
   and verify TLS.
4. Set the env vars from `docs/env-config.md` in the service environment
   (Coolify panel): `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_CLOUD_API_TOKEN`,
   `WHATSAPP_PHONE_NUMBER_ID`.
5. Optional brain/desk proxies: `DIFY_AGENT_URL`, `RAGFLOW_URL`, `CHATWOOT_URL`.
6. Run the latency/load smoke (50 concurrent chats), enable Uptime Kuma +
   nightly SQLite backups.

## systemd sketch

```
[Service]
WorkingDirectory=/opt/WapiDesk/backend
Environment=DATABASE_URL=/var/lib/wapidesk/wapidesk.db
ExecStart=/opt/WapiDesk/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
```

## Docker

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Backups

```bash
cp /var/lib/wapidesk/wapidesk.db /backups/wapidesk-$(date +%F).db
```
