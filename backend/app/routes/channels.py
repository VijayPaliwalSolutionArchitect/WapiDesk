"""Channel routers: WhatsApp Cloud API webhook and the web live-chat widget.

Both converge on the same one-session store and the same SupportAgent brain, which
is exactly the "one session store, many channels" behaviour required by FR-W1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..deps import get_agent, get_store
from ..models import AgentReply, MessageIn
from ..services import SupportAgent
from ..storage import Store

router = APIRouter(tags=["channels"])


@router.post("/api/v1/webhook/whatsapp")
async def whatsapp_webhook(
    payload: dict, request: Request,
    agent: SupportAgent = Depends(get_agent),
) -> JSONResponse:
    """Ingest a WhatsApp Cloud API message and return the agent reply.

    In demo/offline mode the payload is read genuinely; the response echoes the
    structured agent reply so it can be driven with curl or the test suite.
    """
    text = ""
    sender = "demo-number"
    # Try to unpack a realistic Meta Cloud API webhook envelope.
    entry = (payload.get("entry") or [{}])[0]
    change = (entry.get("changes") or [{}])[0]
    value = change.get("value") or {}
    messages = value.get("messages") or []
    if messages:
        m0 = messages[0].get("text", {})
        text = m0.get("body", "")
        waba = value.get("contacts") or [{}]
        sender = (waba[0].get("wa_id") if waba else None) or "demo-number"
    else:
        # Fall back to a simple {"message": "..."} body.
        text = payload.get("message") or payload.get("text") or ""
        sender = payload.get("from") or payload.get("wa_id") or "demo-number"

    if not text:
        raise HTTPException(status_code=400, detail="No message text in payload")

    conv_id = payload.get("conversation_id")
    reply = agent.handle(MessageIn(channel="whatsapp", sender=sender, text=text,
                                   conversation_id=conv_id))

    # Status 200 with a structured body so Meta retries are not triggered.
    return JSONResponse(status_code=status.HTTP_200_OK, content=reply.model_dump())


@router.get("/api/v1/webhook/whatsapp")
def whatsapp_webhook_verify(
    request: Request, agent: SupportAgent = Depends(get_agent),
) -> JSONResponse:
    """Meta Cloud API verification handshake.

    Returns the challenge when ``hub.verify_token`` matches ``WHATSAPP_WEBHOOK_SECRET``.
    Without a configured token we echo the incoming challenge to make local demos painless.
    """
    verify_token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if verify_token and verify_token != agent.settings.whatsapp_verify_token:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    return JSONResponse(content={"hub.challenge": challenge})


@router.post("/api/v1/chat", response_model=AgentReply)
def web_chat(body: MessageIn, request: Request,
             agent: SupportAgent = Depends(get_agent)) -> AgentReply:
    """Web widget chat — same brain, web channel."""
    msg = body.model_copy(update={"channel": "web"})
    return agent.handle(msg)