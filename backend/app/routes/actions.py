"""Action-layer routers: orders, bookings and complaint tickets.

Exposes the tool layer the agent calls internally, plus an HTTP surface so the
business systems / third parties can be integrated against real endpoints
(FR-W3 and FR-W4).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_store
from ..models import (
    BookingCreate,
    BookingOut,
    ComplaintCreate,
    ComplaintOut,
    ComplaintResolve,
    OrderStatus,
)
from ..storage import Store

router = APIRouter(prefix="/api/v1", tags=["actions"])


# --- Orders: status lookups (FR-W3) ---
@router.get("/orders/{order_id}/status", response_model=OrderStatus)
def order_status(order_id: str, store: Store = Depends(get_store)) -> OrderStatus:
    order = store.order_status(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return OrderStatus(
        order_id=order["order_id"], customer_id=order["customer_id"],
        status=order["status"], estimated_delivery=order["estimated_delivery"],
        items=order["items"],
    )


# --- Bookings (FR-W3) ---
@router.get("/bookings", response_model=list[BookingOut])
def list_bookings(customer_id: str | None = None,
                  store: Store = Depends(get_store)) -> list[BookingOut]:
    return [BookingOut(**b) for b in store.list_bookings(customer_id)]


@router.post("/bookings", response_model=BookingOut)
def create_booking(body: BookingCreate, store: Store = Depends(get_store)) -> BookingOut:
    b = store.create_booking(body.customer_id, body.service, body.date, body.time, body.notes)
    return BookingOut(**b)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: str, store: Store = Depends(get_store)) -> BookingOut:
    b = store.cancel_booking(booking_id)
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingOut(**b)


# --- Complaints / tickets (FR-W4) ---
@router.post("/complaints", response_model=ComplaintOut)
def create_complaint(body: ComplaintCreate, store: Store = Depends(get_store)) -> ComplaintOut:
    t = store.create_complaint(
        customer_id=body.customer_id,
        channel="web",
        category=body.category, priority=body.priority, description=body.description,
    )
    return ComplaintOut(**t)


@router.get("/complaints", response_model=list[ComplaintOut])
def list_complaints(status: str | None = None,
                    store: Store = Depends(get_store)) -> list[ComplaintOut]:
    return [ComplaintOut(**t) for t in store.list_complaints(status)]


@router.get("/complaints/{ticket_id}", response_model=ComplaintOut)
def get_complaint(ticket_id: str, store: Store = Depends(get_store)) -> ComplaintOut:
    t = store.get_complaint(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ComplaintOut(**t)


@router.post("/complaints/{ticket_id}/escalate", response_model=ComplaintOut)
def escalate_complaint(ticket_id: str, store: Store = Depends(get_store)) -> ComplaintOut:
    t = store.update_complaint_status(ticket_id, "escalated")
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ComplaintOut(**t)


@router.post("/complaints/{ticket_id}/resolve", response_model=ComplaintOut)
def resolve_complaint(ticket_id: str, body: ComplaintResolve,
                      store: Store = Depends(get_store)) -> ComplaintOut:
    t = store.update_complaint_status(ticket_id, "resolved", body.resolution_notes)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ComplaintOut(**t)