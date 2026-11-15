"""Seeded demo data for WapiDesk.

Provides a small realistic "retail + hospitality vertical" so the action layer,
knowledge grounding, memory and handoff can all be demonstrated and tested
end-to-end without any external service. Each seed row carries stable IDs so the
demo URLs and tests can rely on them.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Knowledge base — grounded answers (FR-W2)
# ---------------------------------------------------------------------------
# Each entry behaves like one chunk in RAGFlow: id, category, title, body.
KNOWLEDGE_BASE: list[dict] = [
    {
        "id": "kb-shipping",
        "category": "shipping",
        "title": "Delivery time for standard orders",
        "body": (
            "Standard delivery takes 3 to 5 business days within India and 7 to 12 "
            "business days for international orders. Express delivery ships within 24 "
            "hours and arrives in 1 to 2 business days. Delivery is free on orders above "
            "Rs. 999."
        ),
    },
    {
        "id": "kb-returns",
        "category": "returns",
        "title": "Return and refund policy",
        "body": (
            "Items can be returned within 7 days of delivery if they are unused and in "
            "their original packaging. Refunds are processed to the original payment "
            "method within 5 to 7 business days after we receive the returned item. "
            "Return shipping is free for defective items only."
        ),
    },
    {
        "id": "kb-health",
        "category": "health",
        "title": "Prescription required for some products",
        "body": (
            "Certain wellness products require a valid prescription. Upload it during "
            "checkout or send it to care@wapi.example and our pharmacy team will review "
            "it within 2 hours on business days."
        ),
    },
    {
        "id": "kb-clinic",
        "category": "clinic",
        "title": "How to book a consultation",
        "body": (
            "Consultations can be booked on WhatsApp by typing BOOK, on the website "
            "widget, or by calling our reception between 9am and 6pm. Teleconsult "
            "slots are available same-day; in-clinic slots open daily at 8am."
        ),
    },
    {
        "id": "kb-hours",
        "category": "hours",
        "title": "Support and business hours",
        "body": (
            "Customer support is available on WhatsApp from 9am to 6pm IST, Monday to "
            "Saturday. Automated self-service runs 24/7. Urgent booking or medical "
            "questions outside hours should contact the on-call line."
        ),
    },
    {
        "id": "kb-payment",
        "category": "payments",
        "title": "Accepted payment methods",
        "body": (
            "We accept UPI, Visa, Mastercard, RuPay, net banking and cash on delivery. "
            "All online payments are processed on our PCI-DSS compliant gateway. "
            "International cards are supported for export orders."
        ),
    },
    {
        "id": "kb-orderlookup",
        "category": "orders",
        "title": "How to check your order status",
        "body": (
            "Send the word STATUS followed by your order id (for example STATUS ORD-1001) "
            "and the agent will fetch live tracking from our order system, including the "
            "current status and estimated delivery date."
        ),
    },
]

# ---------------------------------------------------------------------------
# Orders (FR-W3 - status lookups)
# ---------------------------------------------------------------------------
ORDERS: list[dict] = [
    {
        "order_id": "ORD-1001",
        "customer_id": "917000000001",
        "status": "shipped",
        "estimated_delivery": "2026-11-15",
        "items": ["Serum 30ml", "Vitamin C moisturiser"],
    },
    {
        "order_id": "ORD-1002",
        "customer_id": "917000000001",
        "status": "processing",
        "estimated_delivery": "2026-11-18",
        "items": ["Night cream 50ml"],
    },
    {
        "order_id": "ORD-2001",
        "customer_id": "917000000002",
        "status": "delivered",
        "estimated_delivery": "2026-11-04",
        "items": ["Ultrasound gel", "Disposable sheets"],
    },
]

# ---------------------------------------------------------------------------
# Bookable services (FR-W3 - booking actions)
# ---------------------------------------------------------------------------
SERVICES: list[str] = [
    "General consultation",
    "Dermatology consult",
    "Dental check-up",
    "Physiotherapy session",
    "Full-body health check",
]

# ---------------------------------------------------------------------------
# Per-customer memory (FR-W5)
# ---------------------------------------------------------------------------
MEMORY: list[dict] = [
    {"customer_id": "917000000001", "key": "preferred_language", "value": "English"},
    {"customer_id": "917000000001", "key": "preferred_city", "value": "Mumbai"},
    {"customer_id": "917000000001", "key": "open_issue", "value": "Waiting on ORD-1002 delivery"},
    {"customer_id": "917000000002", "key": "preferred_language", "value": "Hindi"},
    {"customer_id": "917000000002", "key": "preferred_clinic", "value": "Andheri"},
]

# ---------------------------------------------------------------------------
# Opt-out list (FR-W8)
# ---------------------------------------------------------------------------
OPTED_OUT: list[str] = ["917000000099"]