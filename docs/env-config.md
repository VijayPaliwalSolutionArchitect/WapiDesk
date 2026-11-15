# WapiDesk — Environment Configuration

All settings are environment variables, optionally loaded from a `.env` file in
the `backend/` directory via `pydantic-settings`.

Copy `.env.example` to `.env` and fill in real values for production.

| Variable | Default | Required | Purpose |
|---|---|---|---|
| `APP_NAME` | `WapiDesk API` | no | App title in OpenAPI |
| `APP_VERSION` | `1.0.0` | no | Version label |
| `DEBUG` | `false` | no | Debug mode |
| `DATABASE_URL` | `backend/data/wapidesk.db` | no | SQLite path (`:memory:` for tests) |
| `WHATSAPP_VERIFY_TOKEN` | `""` | yes (prod) | Meta webhook verify token |
| `WHATSAPP_WEBHOOK_SECRET` | `""` | recommended | Webhook signature secret |
| `WHATSAPP_CLOUD_API_TOKEN` | `""` | yes (prod) | Meta Cloud API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | yes (prod) | Meta phone number id |
| `DIFY_AGENT_URL` | `""` | no | External Dify agent proxy |
| `DIFY_AGENT_KEY` | `""` | no | Dify API key |
| `RAGFLOW_URL` | `""` | no | External RAGFlow proxy |
| `RAGFLOW_API_KEY` | `""` | no | RAGFlow API key |
| `CHATWOOT_URL` | `""` | no | Chatwoot proxy base |
| `CHATWOOT_ACCOUNT_ID` | `""` | no | Chatwoot account |
| `CHATWOOT_BOT_TOKEN` | `""` | no | Chatwoot bot token |
| `KNOWLEDGE_MAX_SOURCES` | `3` | no | Max citations per grounded answer |
| `QA_CONFIDENCE_THRESHOLD` | `0.4` | no | Below this → flagged for QA review |
| `DEFAULT_HOURS` | `09:00-18:00` | no | Business hours label |

> **Never commit real tokens.** `.env` is gitignored. Keep secrets in the
> deployment platform's secret store (Coolify / systemd `EnvironmentFile`).
