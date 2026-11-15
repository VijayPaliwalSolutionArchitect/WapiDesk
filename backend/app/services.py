"""Business logic for WapiDesk.

Implements the "brain" behaviour called for by the playbook with a deterministic,
offline engine so the whole agent loop is runnable and testable without any
external LLM service:

* intent classification over the free-text customer message;
* RAG-style grounded retrieval over the seeded knowledge base with source
  citations and confidence scoring (FR-W2);
* action execution for order status (FR-W3), bookings (FR-W3) and complaint
  tickets (FR-W4);
* per-customer memory read/write/forget (FR-W5);
* human handoff with transcript + summary (FR-W6);

A single ``SupportAgent`` class owns the whole conversation loop (one message in,
structured reply out) and is what the routers call.
"""

from __future__ import annotations

import re
from collections import Counter

from . import models as m
from .config import Settings
from .storage import Store

# ---------------------------------------------------------------------------
# Deterministic brain: intent + RAG retrieval
# ---------------------------------------------------------------------------

INTENT_KEYWORDS = {
    "greeting": ["hi", "hello", "hey", "good morning", "good evening", "namaste"],
    "order_status": ["status", "order", "track", "tracking", "where is my", "package", "shipped"],
    "booking": ["book", "appointment", "slot", "consult", "schedule", "reserve", "clinic"],
    "complaint": ["complaint", "refund", "return", "damaged", "defective", "wrong item",
                  "not working", "issue", "problem", "dissatisfied", "broken"],
    "human": ["human", "agent", "person", "representative", "talk to", "executive",
              "customer care", "real person"],
    "broadcast_optout": ["stop messages", "unsubscribe", "opt out", "no more updates", "stop promos"],
    "csat": ["rate", "feedback", "satisfaction", "csat"],
    "thanks": ["thanks", "thank you", "thankyou", "great", "awesome"],
}

# Confidence buckets keyed by how many distinct keywords matched an intent.
_HIT_CONFIDENCE = {1: 0.55, 2: 0.75, 3: 0.9}

# Phrases that override keyword classification (explicit intent wins).
EXPLICIT_INTENT = {
    "human": ["talk to a human", "i want a human", "talk to an agent", "put me through",
              "real person", "human agent", "need a human", "i want to talk to a person"],
    "complaint": ["i want to file a complaint", "file a complaint", "register a complaint"],
    "order_status": ["what is the status of order", "check my order status", "track my order"],
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def score_intent(text: str) -> tuple[str, float]:
    """Return (intent, confidence) for a free-text customer message.

    Decisive and deterministic: an order id in the message is treated as an
    explicit order-status signal; otherwise the intent with the most keyword
    hits wins, with confidence bucketed by hit count.
    """
    lower = text.lower().strip().lstrip("0123456789+ ()-").strip()
    # Explicit full-phrase intents win.
    for intent, phrases in EXPLICIT_INTENT.items():
        if any(p in lower for p in phrases):
            return intent, 0.97
    # An order id is an explicit order-tracking signal (e.g. "STATUS ORD-1002").
    if re.search(r"\bord\s*-?\s*\d+", lower):
        return "order_status", 0.95
    tokens = _tokenize(text)
    if not tokens:
        return "greeting", 0.3
    hits: Counter = Counter()
    for intent, words in INTENT_KEYWORDS.items():
        for w in words:
            if " " in w:
                if w in lower:
                    hits[intent] += 2
            elif w in tokens:
                hits[intent] += 1
    if not hits:
        return "unknown", 0.1
    best, best_hits = hits.most_common(1)[0]
    confidence = _HIT_CONFIDENCE.get(best_hits, 0.95)
    return best, confidence


def retrieve(query: str, docs: list[dict], max_sources: int) -> list[tuple[float, dict]]:
    """Rank knowledge docs by token overlap, return (similarity, doc) best first.

    A doc must share at least one token with the query in its body to be a
    candidate; title-token matches get a half-weight bonus, which disambiguates
    otherwise-equal body overlaps (e.g. a "standard delivery" query where several
    docs mention delivery).
    """
    tokens = _tokenize(query)
    if not tokens or not docs:
        return []
    scored: list[tuple[float, dict]] = []
    for doc in docs:
        body_overlap = len(tokens & _tokenize(doc["body"]))
        if body_overlap == 0:
            continue
        title_overlap = len(tokens & _tokenize(doc["title"]))
        similarity = (body_overlap + 0.5 * title_overlap) / len(tokens)
        scored.append((similarity, doc))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return scored[:max_sources]


def confidence_from_retrieval(scores: list[tuple[float, dict]]) -> float:
    if not scores:
        return 0.0
    return round(max(s[0] for s in scores), 3)


# ---------------------------------------------------------------------------
# The support agent
# ---------------------------------------------------------------------------

class SupportAgent:
    """One-brain conversation loop: message in, structured reply out."""

    def __init__(self, store: Store, settings: Settings | None = None) -> None:
        self.store = store
        self.settings = settings or Settings()

    # --- reply construction helpers ---
    def _sources_for(self, scores: list[tuple[float, dict]]) -> list[m.Source]:
        return [
            m.Source(
                id=doc["id"], title=doc["title"], category=doc["category"],
                snippet=doc["body"][:140] + ("…" if len(doc["body"]) > 140 else ""),
            )
            for _, doc in scores
        ]

    def _memory_context(self, customer_id: str) -> list[str]:
        items = self.store.get_memory(customer_id)
        # Use memory that helps personalise this reply.
        return [f"{it['key']}={it['value']}" for it in items]

    # --- public entrypoint ---
    def handle(self, message: m.MessageIn, conversation_id: str | None = None) -> m.AgentReply:
        """Process one customer message and return the structured agent reply."""
        # Resolve / create the conversation session (one session store per channel).
        # The id may arrive on the message itself (routers) or as an explicit arg.
        resolved_id = message.conversation_id or conversation_id
        conv = self.store.get_conversation(resolved_id) if resolved_id else None
        if not conv:
            conv = self.store.create_conversation(
                resolved_id or f"conv-{message.sender}", message.channel, message.sender
            )
        cid = conv["conversation_id"]
        self.store.append_message(cid, "customer", message.text)

        # Already handed off? The human owns it now (FR-W6 resume is explicit).
        if conv["status"] == "handed_off":
            self.store.append_message(
                cid, "agent",
                "This conversation is with a human agent right now. Say RESUME to bring the AI back.",
            )
            return m.AgentReply(
                conversation_id=cid, reply="This conversation is with a human agent right now. Say RESUME to bring the AI back.",
                intent="handed_off", confidence=1.0,
            )

        intent, confidence = score_intent(message.text)
        reply, action, sources, memory, handed = self._dispatch(
            cid, message, intent, confidence
        )

        self.store.append_message(cid, "agent", reply)
        if handed:
            self.store.set_conversation_status(cid, "handed_off")

        return m.AgentReply(
            conversation_id=cid, reply=reply, intent=intent, confidence=confidence,
            sources=sources, memory_used=memory,
            action_taken=action, handed_to_human=handed,
        )

    def _dispatch(self, cid: str, message: m.MessageIn, intent: str,
                  confidence: float) -> tuple[str, str | None, list, list, bool]:
        """Route an intent to the right behaviour. Returns reply, action, sources, memory, handed."""
        mem = self._memory_context(message.sender)
        knowledge = self.store.knowledge()

        if intent == "greeting":
            return self._greeting(message), None, [], mem, False

        if intent == "order_status":
            return self._answer_order(message), "order_status_lookup", [], mem, False

        if intent == "booking":
            return self._answer_booking(message), None, [], mem, False

        if intent == "complaint":
            return self._answer_complaint(message), "complaint_registered", [], mem, False

        if intent == "human":
            return self._handoff(cid, message), "handoff_initiated", [], mem, True

        if intent == "broadcast_optout":
            self.store.opt_out(message.sender)
            return ("You have been unsubscribed from promotional messages. We'll still "
                    "send order and account updates. Reply STOP ANYTIME to confirm."), \
                "opted_out", [], mem, False

        if intent == "csat":
            return ("After this conversation is resolved, please rate us 1 to 5 in-chat "
                    "so we can keep improving."), None, [], mem, False

        if intent == "thanks":
            return "You're welcome! Anything else I can help with today?", None, [], mem, False

        # default: grounded knowledge answer (RAG)
        ka = self._answer_knowledge(message.text, knowledge)
        return ka.answer, None, ka.sources, mem, False

    # --- knowledge (FR-W2) ---
    def _answer_knowledge(self, text: str, knowledge: list[dict]) -> m.AgentReply:
        scores = retrieve(text, knowledge, self.settings.knowledge_max_sources)
        conf = confidence_from_retrieval(scores)
        sources = self._sources_for(scores)
        if not scores:
            reply = (
                "I couldn't find that in our knowledge base. I'll flag this for our team "
                "to review — meanwhile, would you like to check an order, make a booking, "
                "or file a complaint?"
            )
        else:
            _, doc = scores[0]
            reply = f"{doc['body']} (source: {doc['title']})"
        flagged = conf < self.settings.qa_confidence_threshold
        return m.KnowledgeAnswer(
            question=text, answer=reply, sources=sources,
            confidence=conf, flagged_for_qa=flagged,
        )

    # --- orders (FR-W3) ---
    def _answer_order(self, message: m.MessageIn) -> str:
        match = re.search(r"(ord[-:]?\s*\w+)", message.text.lower())
        if match:
            order_id = match.group(1).replace("-", "-").upper()
        else:
            order_id = "ORD-1001"  # demo fallback
        order = self.store.order_status(order_id)
        if not order:
            return f"I couldn't find an order matching {order_id}. Double-check the id and try again."
        self.store.set_memory(message.sender, "last_order", order_id)
        return (
            f"Order {order['order_id']} for {message.sender}: status is "
            f"{order['status']}, estimated delivery {order['estimated_delivery']}. "
            f"Items: {', '.join(order['items'])}."
        )

    # --- bookings (FR-W3) ---
    def _answer_booking(self, message: m.MessageIn) -> str:
        # Try to parse "BOOK <service> on <date> at <time>"
        match = re.search(r"book\s+([a-z\s-]+?)\s+on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2})",
                          message.text.lower())
        if match:
            service = match.group(1).strip().title()
            date, time = match.group(2), match.group(3) + ":00" if len(match.group(3)) == len("00:00") else match.group(3)
            b = self.store.create_booking(message.sender, service, date, time)
            self.store.set_memory(message.sender, "next_booking", b["booking_id"])
            return (f"Confirmed booking {b['booking_id']}: {service} on {date} at {time}. "
                    "Reply CANCEL <id> to cancel.")
        # Otherwise show availability + how to book.
        return (
            "I can book a consultation for you. Available services: General consultation, "
            "Dermatology consult, Dental check-up, Physiotherapy session, Full-body health "
            "check. Reply like: BOOK Dermatology consult on 2026-11-20 at 14:30"
        )

    # --- complaints (FR-W4) ---
    def _answer_complaint(self, message: m.MessageIn) -> str:
        category = "general"
        for cat in ["order", "delivery", "refund", "product", "booking"]:
            if cat in message.text.lower():
                category = cat
                break
        ticket = self.store.create_complaint(
            customer_id=message.sender, channel=message.channel,
            category=category, priority="medium", description=message.text,
        )
        self.store.set_memory(message.sender, "open_ticket", ticket["ticket_id"])
        return (
            f"Your complaint has been registered as ticket {ticket['ticket_id']} "
            f"(category: {category}, SLA: {ticket['sla_timestamp'][:16].replace('T', ' ')}). "
            "Our team will acknowledge it today; reply STATUS to check progress."
        )

    # --- handoff (FR-W6) ---
    def _handoff(self, cid: str, message: m.MessageIn) -> str:
        conv = self.store.get_conversation(cid)
        transcript = conv["messages"]
        summary = self._summarise(transcript)
        self.store.set_conversation_status(cid, "handed_off", summary)
        return (
            "I've handed you to a human agent with the full conversation context. "
            "Please hold on — the team will reply shortly. Once resolved, say RESUME "
            "and I'll take back over."
        )

    @staticmethod
    def _summarise(messages: list[dict]) -> str:
        customer_lines = [mm["text"] for mm in messages if mm["role"] == "customer"]
        if not customer_lines:
            return "No customer messages yet."
        preview = " | ".join(customer_lines[-4:])
        return f"Customer contact handled via AI; last messages: {preview}"

    def _greeting(self, message: m.MessageIn) -> str:
        prefs = self.store.get_memory(message.sender)
        name_hint = next((it["value"] for it in prefs if "name" in it["key"]), "")
        salutation = f"Hi {name_hint}," if name_hint else "Hi there,"
        return (
            f"{salutation} welcome to WapiDesk support! I can check your order (STATUS <id>), "
            "book a consultation, file a complaint, or answer questions about our services. "
            "How can I help today?"
        )