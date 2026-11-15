"""Ops routers: knowledge query, CSAT, broadcasts + opt-out and stats dashboard.

Covers FR-W2 (grounded answers with citations on request), FR-W7 (CSAT capture and
trends) and FR-W8 (approved broadcasts with opt-out handling), plus the QA flag
surface (FR-W9) that powers the ops dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_agent, get_store
from ..models import (
    BroadcastCreate,
    BroadcastOut,
    CsatIn,
    CsatOut,
    CsatStats,
    KnowledgeAnswer,
    OptOutBody,
    QaFlag,
)
from ..services import (
    SupportAgent,
    confidence_from_retrieval,
    retrieve,
)
from ..storage import Store

router = APIRouter(prefix="/api/v1", tags=["ops"])


# --- Knowledge (FR-W2) ---
@router.get("/knowledge", response_model=KnowledgeAnswer)
def knowledge_query(q: str, agent: SupportAgent = Depends(get_agent)) -> KnowledgeAnswer:
    """Ground a free-text question in the knowledge base and return citations."""
    return agent._answer_knowledge(q, agent.store.knowledge())


@router.get("/knowledge/list", response_model=list)
def knowledge_list(store: Store = Depends(get_store)) -> list:
    return store.knowledge()


# --- CSAT (FR-W7) ---
@router.post("/csat", response_model=CsatOut)
def submit_csat(body: CsatIn, store: Store = Depends(get_store)) -> CsatOut:
    if store.get_conversation(body.conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    rec = store.save_csat(body.conversation_id, body.rating, body.comment)
    return CsatOut(**rec)


@router.get("/stats/csat", response_model=CsatStats)
def csat_stats(store: Store = Depends(get_store)) -> CsatStats:
    rows = store.csat_rows()
    if not rows:
        return CsatStats(count=0, average=0.0, trend=[])
    avg = round(sum(r["rating"] for r in rows) / len(rows), 2)
    # Per-day trend for the dashboard.
    buckets: dict[str, list[int]] = {}
    for r in rows:
        day = r["created_at"][:10]
        buckets.setdefault(day, []).append(r["rating"])
    trend = [{"date": d, "avg": round(sum(v) / len(v), 2), "n": len(v)}
             for d, v in sorted(buckets.items())]
    return CsatStats(count=len(rows), average=avg, trend=trend)


# --- Broadcasts / opt-out (FR-W8) ---
@router.post("/broadcasts", response_model=BroadcastOut)
def create_broadcast(body: BroadcastCreate, store: Store = Depends(get_store)) -> BroadcastOut:
    customers = store.list_conversation_customer_ids()
    opted = store.opted_out_ids()
    recipients = [c for c in customers if body.audience == "all" or c not in opted]
    skipped = len(customers) - len(recipients)
    rec = store.create_broadcast(body.template, len(recipients), skipped)
    return BroadcastOut(**rec)


@router.get("/broadcasts", response_model=list[BroadcastOut])
def list_broadcasts(store: Store = Depends(get_store)) -> list[BroadcastOut]:
    return [BroadcastOut(**b) for b in store.list_broadcasts()]


@router.post("/optout", response_model=dict)
def opt_out(body: OptOutBody, store: Store = Depends(get_store)) -> dict:
    store.opt_out(body.customer_id)
    return {"customer_id": body.customer_id, "opted_out": True}


# --- QA flags (FR-W9) ---
@router.get("/stats/qa-flags", response_model=list[QaFlag])
def qa_flags(agent: SupportAgent = Depends(get_agent)) -> list[QaFlag]:
    """Flag low-confidence knowledge conversations for supervisor review."""
    store = agent.store
    flags: list[QaFlag] = []
    threshold = agent.settings.qa_confidence_threshold
    for conv in store.list_conversations():
        # Recompute retrieval confidence against each customer knowledge query.
        for mm in conv["messages"]:
            if mm["role"] != "customer":
                continue
            scores = retrieve(mm["text"], store.knowledge(), agent.settings.knowledge_max_sources)
            conf = confidence_from_retrieval(scores)
            if scores and conf < threshold:
                flags.append(QaFlag(
                    conversation_id=conv["conversation_id"],
                    reason=f"Low retrieval confidence {conf} on: {mm['text'][:80]}",
                    confidence=conf, flagged_at=mm["ts"],
                ))
                break
    return flags