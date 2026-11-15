"""Desk routers: conversations, memory and human handoff.

Implements the human-takeover experience described by FR-W1 / FR-W5 / FR-W6 —
transcript + summary on takeover, and explicit resume back to the AI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_agent, get_store
from ..models import (
    ConversationOut,
    HandoffReceipt,
    MemoryOut,
    ConversationMessage,
)
from ..services import SupportAgent
from ..storage import Store

router = APIRouter(prefix="/api/v1/desk", tags=["desk"])


def _conv_out(conv: dict) -> ConversationOut:
    conv["messages"] = [
        ConversationMessage(id=mm["id"], role=mm["role"], text=mm["text"], ts=mm["ts"])
        for mm in conv["messages"]
    ]
    return ConversationOut(**conv)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(status: str | None = None,
                       store: Store = Depends(get_store)) -> list[ConversationOut]:
    return [_conv_out(c) for c in store.list_conversations(status)]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, store: Store = Depends(get_store)) -> ConversationOut:
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_out(conv)


@router.post("/conversations/{conversation_id}/handoff", response_model=HandoffReceipt)
def handoff(conversation_id: str, store: Store = Depends(get_store)) -> HandoffReceipt:
    """Open the human inbox with transcript + summary (FR-W6 Handoff demo moment)."""
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    summary = (conv.get("summary")
               or SupportAgent._summarise(conv["messages"]))
    store.set_conversation_status(conversation_id, "handed_off", summary)
    conv = store.get_conversation(conversation_id)
    suggested = ["Review recent order", "Confirm booking slot", "Reply within SLA"]
    return HandoffReceipt(
        conversation_id=conversation_id, status=conv["status"],
        transcript=conv["messages"], summary=summary, suggested_actions=suggested,
    )


@router.post("/conversations/{conversation_id}/resume", response_model=ConversationOut)
def resume(conversation_id: str, store: Store = Depends(get_store)) -> ConversationOut:
    """Close the human handoff and let the AI take the conversation back (FR-W6)."""
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = store.set_conversation_status(conversation_id, "active")
    store.append_message(
        conversation_id, "agent",
        "Hi, the AI assistant is back and has full context. How can I continue helping?",
    )
    updated = store.get_conversation(conversation_id)
    return _conv_out(updated)


# --- per-customer memory (FR-W5) ---
@router.get("/memory/{customer_id}", response_model=MemoryOut)
def get_memory(customer_id: str, store: Store = Depends(get_store)) -> MemoryOut:
    items = store.get_memory(customer_id)
    return MemoryOut(
        customer_id=customer_id,
        items=[{"key": it["key"], "value": it["value"], "updated_at": it["updated_at"]} for it in items],
    )


@router.delete("/memory/{customer_id}", response_model=dict)
def forget_memory(customer_id: str, key: str | None = None,
                  store: Store = Depends(get_store)) -> dict:
    """Right-to-forget: edit/forget controls for customer memory (FR-W5)."""
    deleted = store.forget_memory(customer_id, key)
    return {"customer_id": customer_id, "deleted_items": deleted}