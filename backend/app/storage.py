"""Persistence layer for WapiDesk.

Uses the Python standard library ``sqlite3`` so the service has zero database
dependencies beyond the interpreter. A single ``Store`` class owns the schema,
seeding and all data access; the FastAPI app holds one instance (see ``main.py``
and the router dependency).

Default persistence path is ``backend/data/wapidesk.db`` (git-ignored) unless
``DATABASE_URL`` is set — the test suite uses ``:memory:``.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .seed_data import (
    KNOWLEDGE_BASE,
    MEMORY,
    OPTED_OUT,
    ORDERS,
    SERVICES,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    estimated_delivery TEXT NOT NULL,
    items TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    service TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    cancelled_at TEXT
);

CREATE TABLE IF NOT EXISTS complaints (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolution_notes TEXT,
    sla_timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    messages TEXT NOT NULL,
    status TEXT NOT NULL,
    handed_off_at TEXT,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS memory (
    customer_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (customer_id, key)
);

CREATE TABLE IF NOT EXISTS optout (
    customer_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS csat (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS broadcast(
    broadcast_id TEXT PRIMARY KEY,
    template TEXT NOT NULL,
    status TEXT NOT NULL,
    recipients INTEGER NOT NULL,
    opted_out_skipped INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _load(value: str) -> list[Any]:
    return json.loads(value or "[]")


def _dump(value: Any) -> str:
    return json.dumps(value)


class Store:
    """Owns the SQLite connection, schema bootstrap and all data access."""

    def __init__(self, database_url: str = ":memory:", seed: bool = True) -> None:
        in_memory = database_url == ":memory:"
        if not in_memory:
            Path(database_url).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(database_url, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
        if seed:
            self.seed()

    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def seed(self) -> None:
        """Idempotently load the demo data set."""
        for doc in KNOWLEDGE_BASE:
            self.conn.execute(
                "INSERT OR IGNORE INTO knowledge (id, category, title, body) "
                "VALUES (?,?,?,?)",
                (doc["id"], doc["category"], doc["title"], doc["body"]),
            )
        for o in ORDERS:
            self.conn.execute(
                "INSERT OR IGNORE INTO orders (order_id, customer_id, status, "
                "estimated_delivery, items) VALUES (?,?,?,?,?)",
                (o["order_id"], o["customer_id"], o["status"],
                 o["estimated_delivery"], _dump(o["items"])),
            )
        for s in SERVICES:
            self.conn.execute("INSERT OR IGNORE INTO services (name) VALUES (?)", (s,))
        for m in MEMORY:
            self.conn.execute(
                "INSERT OR IGNORE INTO memory (customer_id, key, value, updated_at) "
                "VALUES (?,?,?,?)",
                (m["customer_id"], m["key"], m["value"], _now()),
            )
        for cid in OPTED_OUT:
            self.conn.execute("INSERT OR IGNORE INTO optout (customer_id) VALUES (?)", (cid,))
        self.conn.commit()

    # --- Knowledge (FR-W2) ---
    def knowledge(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, category, title, body FROM knowledge"
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Orders (FR-W3) ---
    def order_status(self, order_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT order_id, customer_id, status, estimated_delivery, items "
            "FROM orders WHERE lower(order_id)=?",
            (order_id.lower(),),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["items"] = _load(d["items"])
        return d

    # --- Bookings (FR-W3) ---
    def create_booking(self, customer_id: str, service: str, date: str,
                       time: str, notes: str = "") -> dict:
        bid = _uid("BK")
        created = _now()
        self.conn.execute(
            "INSERT INTO bookings (booking_id, customer_id, service, date, time, "
            "status, created_at, cancelled_at) VALUES (?,?,?,?,?,?,?,?)",
            (bid, customer_id, service, date, time, "confirmed", created, None),
        )
        self.conn.commit()
        return self.get_booking(bid)

    def get_booking(self, booking_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM bookings WHERE booking_id=?", (booking_id,)
        ).fetchone()
        return dict(row) if row else None

    def cancel_booking(self, booking_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
        if not row:
            return None
        self.conn.execute(
            "UPDATE bookings SET status=?, cancelled_at=? WHERE booking_id=?",
            ("cancelled", _now(), booking_id),
        )
        self.conn.commit()
        return self.get_booking(booking_id)

    def list_bookings(self, customer_id: str | None = None) -> list[dict]:
        if customer_id:
            rows = self.conn.execute(
                "SELECT * FROM bookings WHERE customer_id=? ORDER BY created_at", (customer_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM bookings ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]

    # --- Complaints / tickets (FR-W4) ---
    def create_complaint(self, customer_id: str, channel: str, category: str,
                         priority: str, description: str) -> dict:
        tid = _uid("TK")
        now = _now()
        sla = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        self.conn.execute(
            "INSERT INTO complaints (ticket_id, customer_id, channel, category, "
            "priority, description, status, created_at, updated_at, resolution_notes, "
            "sla_timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (tid, customer_id, channel, category, priority, description,
             "open", now, now, None, sla),
        )
        self.conn.commit()
        return self.get_complaint(tid)

    def get_complaint(self, ticket_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM complaints WHERE ticket_id=?", (ticket_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_complaint_status(self, ticket_id: str, status: str,
                                resolution_notes: str | None = None) -> dict | None:
        existing = self.get_complaint(ticket_id)
        if not existing:
            return None
        self.conn.execute(
            "UPDATE complaints SET status=?, updated_at=?, resolution_notes=? "
            "WHERE ticket_id=?",
            (status, _now(), resolution_notes, ticket_id),
        )
        self.conn.commit()
        return self.get_complaint(ticket_id)

    def list_complaints(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM complaints WHERE status=? ORDER BY created_at", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM complaints ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]

    # --- Conversations (FR-W1) ---
    def get_conversation(self, conversation_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM conversations WHERE conversation_id=?", (conversation_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["messages"] = _load(d["messages"])
        return d

    def create_conversation(self, conversation_id: str, channel: str,
                            customer_id: str) -> dict:
        self.conn.execute(
            "INSERT INTO conversations (conversation_id, channel, customer_id, "
            "messages, status, handed_off_at, summary) VALUES (?,?,?,?,?,?,?)",
            (conversation_id, channel, customer_id, _dump([]), "active", None, None),
        )
        self.conn.commit()
        return self.get_conversation(conversation_id)

    def append_message(self, conversation_id: str, role: str, text: str) -> None:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return
        msg = {"id": _uid("MSG"), "role": role, "text": text, "ts": _now()}
        conv["messages"].append(msg)
        self.conn.execute(
            "UPDATE conversations SET messages=? WHERE conversation_id=?",
            (_dump(conv["messages"]), conversation_id),
        )
        self.conn.commit()

    def set_conversation_status(self, conversation_id: str, status: str,
                                summary: str | None = None) -> dict | None:
        existing = self.get_conversation(conversation_id)
        if not existing:
            return None
        self.conn.execute(
            "UPDATE conversations SET status=?, summary=COALESCE(?, summary) "
            "WHERE conversation_id=?",
            (status, summary, conversation_id),
        )
        self.conn.commit()
        return self.get_conversation(conversation_id)

    def list_conversations(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM conversations WHERE status=? ORDER BY rowid DESC", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM conversations ORDER BY rowid DESC").fetchall()
        return [dict(r) for r in rows]

    # --- Memory (FR-W5) ---
    def get_memory(self, customer_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT key, value, updated_at FROM memory WHERE customer_id=? "
            "ORDER BY key",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def set_memory(self, customer_id: str, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO memory (customer_id, key, value, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(customer_id, key) DO UPDATE SET value=excluded.value, "
            "updated_at=excluded.updated_at",
            (customer_id, key, value, _now()),
        )
        self.conn.commit()

    def forget_memory(self, customer_id: str, key: str | None = None) -> int:
        if key:
            cur = self.conn.execute(
                "DELETE FROM memory WHERE customer_id=? AND key=?", (customer_id, key)
            )
        else:
            cur = self.conn.execute("DELETE FROM memory WHERE customer_id=?", (customer_id,))
        self.conn.commit()
        return cur.rowcount

    # --- Opt-out (FR-W8) ---
    def is_opted_out(self, customer_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM optout WHERE customer_id=?", (customer_id,)
        ).fetchone()
        return row is not None

    def opt_out(self, customer_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO optout (customer_id) VALUES (?)", (customer_id,)
        )
        self.conn.commit()

    def opted_out_ids(self) -> list[str]:
        rows = self.conn.execute("SELECT customer_id FROM optout").fetchall()
        return [r["customer_id"] for r in rows]

    # --- CSAT (FR-W7) ---
    def save_csat(self, conversation_id: str, rating: int, comment: str) -> dict:
        cid = _uid("CSAT")
        created = _now()
        self.conn.execute(
            "INSERT INTO csat (id, conversation_id, rating, comment, created_at) "
            "VALUES (?,?,?,?,?)",
            (cid, conversation_id, rating, comment, created),
        )
        self.conn.commit()
        return {"id": cid, "conversation_id": conversation_id, "rating": rating,
                "comment": comment, "created_at": created}

    def csat_rows(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, conversation_id, rating, comment, created_at FROM csat ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_conversation_customer_ids(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT customer_id FROM conversations"
        ).fetchall()
        return [r["customer_id"] for r in rows]

    # --- Broadcasts (FR-W8) ---
    def create_broadcast(self, template: str, recipients: int, skipped: int) -> dict:
        bid = _uid("BC")
        created = _now()
        self.conn.execute(
            "INSERT INTO broadcast (broadcast_id, template, status, recipients, "
            "opted_out_skipped, created_at) VALUES (?,?,?,?,?,?)",
            (bid, template, "queued", recipients, skipped, created),
        )
        self.conn.commit()
        return {"broadcast_id": bid, "template": template, "status": "queued",
                "recipients": recipients, "opted_out_skipped": skipped,
                "created_at": created}

    def list_broadcasts(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM broadcast ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()