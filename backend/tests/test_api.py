"""End-to-end API tests for WapiDesk.

Covers the demo/acceptance path from the playbook chapter:
cited knowledge answer -> order lookup -> complaint ticket -> human handoff ->
CSAT -> memory + broadcast/opt-out.
"""

from __future__ import annotations


def _chat(client, sender: str, text: str, conversation_id: str | None = None):
    payload = {"channel": "web", "sender": sender, "text": text}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return client.post("/api/v1/chat", json=payload)


# --------------------------------------------------------------------------
# System
# --------------------------------------------------------------------------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# --------------------------------------------------------------------------
# Channels / brain (FR-W1, FR-W2)
# --------------------------------------------------------------------------
def test_knowledge_answer_has_citations(client):
    r = client.get("/api/v1/knowledge", params={"q": "how long does standard delivery take"})
    assert r.status_code == 200
    body = r.json()
    assert "business days" in body["answer"].lower()
    assert body["sources"], "expected at least one grounded source citation"


def test_web_chat_returns_reply_and_conversation(client):
    r = _chat(client, "test-customer-1", "What is your delivery time?")
    assert r.status_code == 200
    body = r.json()
    assert body["conversation_id"]
    assert "delivery" in body["reply"].lower()
    # Same session store reused across messages.
    r2 = _chat(client, "test-customer-1", "thanks", body["conversation_id"])
    assert r2.json()["conversation_id"] == body["conversation_id"]


def test_whatsapp_webhook_verification(client):
    r = client.get("/api/v1/webhook/whatsapp",
                   params={"hub.mode": "subscribe", "hub.challenge": "12345"})
    assert r.status_code == 200
    assert r.json()["hub.challenge"] == "12345"


def test_whatsapp_webhook_ingest(client):
    payload = {
        "entry": [{"id": "0", "changes": [{"value": {
            "messages": [{"from": "917000000007",
                          "text": {"body": "STATUS ORD-1002"}}],
            "contacts": [{"wa_id": "917000000007"}],
        }}]}],
    }
    r = client.post("/api/v1/webhook/whatsapp", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "order_status"
    assert "ORD-1002" in body["reply"]


# --------------------------------------------------------------------------
# Action layer (FR-W3, FR-W4)
# --------------------------------------------------------------------------
def test_order_status_endpoint(client):
    r = client.get("/api/v1/orders/ORD-1001/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "shipped"
    assert any("Serum" in item for item in body["items"])
    assert client.get("/api/v1/orders/UNKNOWN/status").status_code == 404


def test_booking_create_and_cancel(client):
    create = client.post("/api/v1/bookings", json={
        "customer_id": "917000000001", "service": "Dental check-up",
        "date": "2026-11-20", "time": "14:30",
    })
    assert create.status_code == 200
    bid = create.json()["booking_id"]
    assert create.json()["status"] == "confirmed"

    cancel = client.post(f"/api/v1/bookings/{bid}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"


def test_complaint_lifecycle(client):
    r = client.post("/api/v1/complaints", json={
        "customer_id": "917000000001", "customer_contact": "917000000001",
        "category": "delivery", "priority": "high",
        "description": "Package arrived damaged",
    })
    assert r.status_code == 200
    t = r.json()
    assert t["status"] == "open"
    assert t["sla_timestamp"]

    es = client.post(f"/api/v1/complaints/{t['ticket_id']}/escalate")
    assert es.json()["status"] == "escalated"

    rs = client.post(f"/api/v1/complaints/{t['ticket_id']}/resolve",
                     json={"resolution_notes": "Replacement dispatched"})
    assert rs.json()["status"] == "resolved"
    assert rs.json()["resolution_notes"] == "Replacement dispatched"

    assert client.get("/api/v1/complaints").json()  # non-empty list


def test_complaint_via_chat(client):
    r = _chat(client, "917000000002", "I want to file a complaint, my order is damaged")
    assert r.json()["action_taken"] == "complaint_registered"
    assert r.json()["intent"] == "complaint"


# --------------------------------------------------------------------------
# Handoff (FR-W6)
# --------------------------------------------------------------------------
def test_handoff_and_resume(client):
    chat = _chat(client, "917000000001", "I need a human please")
    cid = chat.json()["conversation_id"]
    assert chat.json()["handed_to_human"] is True

    conv = client.get(f"/api/v1/desk/conversations/{cid}")
    assert conv.json()["status"] == "handed_off"

    handoff = client.post(f"/api/v1/desk/conversations/{cid}/handoff")
    assert handoff.status_code == 200
    receipt = handoff.json()
    assert receipt["status"] == "handed_off"
    assert receipt["transcript"]
    assert receipt["summary"]

    resume = client.post(f"/api/v1/desk/conversations/{cid}/resume")
    assert resume.json()["status"] == "active"


# --------------------------------------------------------------------------
# CSAT (FR-W7)
# --------------------------------------------------------------------------
def test_csat_capture_and_stats(client):
    chat = _chat(client, "917000000001", "hello")
    cid = chat.json()["conversation_id"]
    r = client.post("/api/v1/csat", json={"conversation_id": cid, "rating": 5,
                                          "comment": "fast"})
    assert r.status_code == 200
    stats = client.get("/api/v1/stats/csat").json()
    assert stats["count"] == 1
    assert stats["average"] == 5.0
    assert stats["trend"][0]["avg"] == 5.0


# --------------------------------------------------------------------------
# Memory / broadcasts / opt-out (FR-W5, FR-W8)
# --------------------------------------------------------------------------
def test_memory_forget(client):
    r = _chat(client, "917000000001", "STATUS ORD-1001")
    assert r.status_code == 200
    mem = client.get("/api/v1/desk/memory/917000000001").json()
    keys = [it["key"] for it in mem["items"]]
    assert "last_order" in keys

    forget = client.delete("/api/v1/desk/memory/917000000001")
    assert forget.json()["deleted_items"] >= 1
    assert client.get("/api/v1/desk/memory/917000000001").json()["items"] == []


def test_broadcast_skips_opted_out(client):
    # Seed the conversation store with a couple of customer ids.
    _chat(client, "917000000001", "hello")
    _chat(client, "917000000099", "hello")  # 917000000099 is pre-opted-out
    r = client.post("/api/v1/broadcasts", json={"template": "Fresh stock is here!",
                                                "audience": "opted_in"})
    assert r.status_code == 200
    b = r.json()
    assert b["recipients"] >= 1
    assert b["opted_out_skipped"] >= 1


def test_opt_out_endpoint(client):
    r = client.post("/api/v1/optout", json={"customer_id": "917000000001"})
    assert r.json()["opted_out"] is True