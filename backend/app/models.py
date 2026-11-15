"""Pydantic request / response schemas for the WapiDesk API.

These match the entities described in the playbook: knowledge answers with
citations, order status, bookings, complaint tickets, conversations/memory,
handoff, CSAT and broadcasts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------
class Source(BaseModel):
    """A grounded source citation returned with a knowledge answer."""

    id: str
    title: str
    category: str
    snippet: str


class KnowledgeAnswer(BaseModel):
    """RAG-style answer with source citations (FR-W2)."""

    question: str
    answer: str
    sources: list[Source] = Field(default_factory=list)
    confidence: float
    flagged_for_qa: bool = False


class MessageIn(BaseModel):
    """An inbound customer message from WhatsApp or the web widget."""

    channel: Literal["whatsapp", "web"] = "whatsapp"
    sender: str = Field(..., description="Phone number (whatsapp) or session id (web)")
    text: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentReply(BaseModel):
    """The agent's reply to a single inbound message."""

    conversation_id: str
    reply: str
    intent: str
    confidence: float
    sources: list[Source] = Field(default_factory=list)
    memory_used: list[str] = Field(default_factory=list)
    action_taken: Optional[str] = None
    handed_to_human: bool = False


# ---------------------------------------------------------------------------
# Orders (FR-W3 - lookups)
# ---------------------------------------------------------------------------
class OrderStatus(BaseModel):
    order_id: str
    customer_id: str
    status: str
    estimated_delivery: str
    items: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Bookings (FR-W3 - actions)
# ---------------------------------------------------------------------------
class BookingCreate(BaseModel):
    customer_id: str
    customer_name: str = ""
    service: str
    date: str
    time: str
    notes: str = ""


class BookingOut(BaseModel):
    booking_id: str
    customer_id: str
    service: str
    date: str
    time: str
    status: str
    created_at: datetime
    cancelled_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Complaints / tickets (FR-W4)
# ---------------------------------------------------------------------------
class ComplaintCreate(BaseModel):
    customer_id: str
    customer_contact: str
    category: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    description: str = Field(..., min_length=3)


class ComplaintResolve(BaseModel):
    resolution_notes: str


class ComplaintOut(BaseModel):
    ticket_id: str
    customer_id: str
    category: str
    priority: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    resolution_notes: Optional[str] = None
    sla_timestamp: datetime


# ---------------------------------------------------------------------------
# Conversations / memory (FR-W1, FR-W5)
# ---------------------------------------------------------------------------
class ConversationMessage(BaseModel):
    id: str
    role: Literal["customer", "agent"]
    text: str
    ts: datetime


class ConversationOut(BaseModel):
    conversation_id: str
    channel: str
    customer_id: str
    messages: list[ConversationMessage] = Field(default_factory=list)
    status: Literal["active", "handed_off", "resolved"] = "active"
    handed_off_at: Optional[datetime] = None
    summary: Optional[str] = None


class HandoffReceipt(BaseModel):
    conversation_id: str
    status: str
    transcript: list[ConversationMessage] = Field(default_factory=list)
    summary: str
    suggested_actions: list[str] = Field(default_factory=list)


class MemoryItem(BaseModel):
    key: str
    value: str
    updated_at: datetime


class MemoryOut(BaseModel):
    customer_id: str
    items: list[MemoryItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CSAT (FR-W7)
# ---------------------------------------------------------------------------
class CsatIn(BaseModel):
    conversation_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""


class CsatOut(BaseModel):
    id: str
    conversation_id: str
    rating: int
    comment: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Broadcasts / opt-out (FR-W8)
# ---------------------------------------------------------------------------
class BroadcastCreate(BaseModel):
    template: str
    audience: Literal["all", "opted_in"] = "opted_in"
    scheduled_at: Optional[datetime] = None


class BroadcastOut(BaseModel):
    broadcast_id: str
    template: str
    status: str
    recipients: int
    opted_out_skipped: int
    created_at: datetime


class OptOutBody(BaseModel):
    customer_id: str


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
class CsatStats(BaseModel):
    count: int
    average: float
    trend: list[dict[str, Any]] = Field(default_factory=list)


class QaFlag(BaseModel):
    conversation_id: str
    reason: str
    confidence: float
    flagged_at: datetime