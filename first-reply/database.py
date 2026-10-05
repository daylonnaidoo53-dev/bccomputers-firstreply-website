"""
database.py — SQLite storage for leads and senders.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH: Path | str = Path(__file__).resolve().parent / "leads.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(custom_path: Optional[Path | str] = None) -> None:
    """Initialize SQLite database tables and indexes."""
    global DB_PATH
    if custom_path is not None:
        DB_PATH = custom_path

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                channel            TEXT    NOT NULL,
                sender_id          TEXT    NOT NULL,
                sender_name        TEXT,
                text               TEXT    NOT NULL,
                received_at        TEXT    NOT NULL,
                reply_text         TEXT,
                reply_sent_at      TEXT,
                replied_within_sla INTEGER DEFAULT 0,
                booked_slot        TEXT,
                owner_took_over_at TEXT,
                bot_on             INTEGER DEFAULT 1,
                opted_out          INTEGER DEFAULT 0,
                auto_reply_sent    INTEGER DEFAULT 0,
                last_auto_reply_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_leads_sender
            ON leads (channel, sender_id)
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS senders (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                channel            TEXT    NOT NULL,
                sender_id          TEXT    NOT NULL,
                opted_out          INTEGER DEFAULT 0,
                last_auto_reply_at TEXT,
                owner_owned        INTEGER DEFAULT 0,
                bot_on             INTEGER DEFAULT 1,
                UNIQUE(channel, sender_id)
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_senders_unique
            ON senders (channel, sender_id)
            """
        )


def insert_lead(
    channel: str,
    sender_id: str,
    sender_name: str,
    text: str,
    received_at: datetime,
) -> int:
    """Insert a new incoming lead record. Returns inserted row ID."""
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO leads (channel, sender_id, sender_name, text, received_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (channel, sender_id, sender_name, text, received_at.isoformat()),
        )
        # Ensure sender entry exists
        conn.execute(
            """
            INSERT INTO senders (channel, sender_id)
            VALUES (?, ?)
            ON CONFLICT(channel, sender_id) DO NOTHING
            """,
            (channel, sender_id),
        )
        return int(cur.lastrowid)


def update_reply(
    lead_id: int,
    reply_text: str,
    reply_sent_at: datetime,
    replied_within_sla: bool,
) -> None:
    """Record auto-reply timestamp, content, and SLA compliance."""
    sent_iso = reply_sent_at.isoformat()
    sla_val = 1 if replied_within_sla else 0

    with _connect() as conn:
        conn.execute(
            """
            UPDATE leads
            SET reply_text = ?,
                reply_sent_at = ?,
                replied_within_sla = ?,
                auto_reply_sent = 1,
                last_auto_reply_at = ?
            WHERE id = ?
            """,
            (reply_text, sent_iso, sla_val, sent_iso, lead_id),
        )

        row = conn.execute(
            "SELECT channel, sender_id FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row:
            conn.execute(
                """
                INSERT INTO senders (channel, sender_id, last_auto_reply_at)
                VALUES (?, ?, ?)
                ON CONFLICT(channel, sender_id) DO UPDATE SET
                    last_auto_reply_at = excluded.last_auto_reply_at
                """,
                (row["channel"], row["sender_id"], sent_iso),
            )


def mark_opted_out(channel: str, sender_id: str) -> None:
    """Upsert sender opt-out status."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO senders (channel, sender_id, opted_out)
            VALUES (?, ?, 1)
            ON CONFLICT(channel, sender_id) DO UPDATE SET opted_out = 1
            """,
            (channel, sender_id),
        )
        conn.execute(
            "UPDATE leads SET opted_out = 1 WHERE channel = ? AND sender_id = ?",
            (channel, sender_id),
        )


def is_opted_out(channel: str, sender_id: str) -> bool:
    """Check if a sender has opted out on this channel."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT opted_out FROM senders WHERE channel = ? AND sender_id = ?",
            (channel, sender_id),
        ).fetchone()
        if row:
            return bool(row["opted_out"])

        lead_row = conn.execute(
            """
            SELECT opted_out FROM leads
            WHERE channel = ? AND sender_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (channel, sender_id),
        ).fetchone()
        return bool(lead_row and lead_row["opted_out"])


def mark_owner_takeover(lead_id: int) -> None:
    """Mark a thread as owner-owned after TAKE command."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE leads
            SET owner_took_over_at = ?, bot_on = 0
            WHERE id = ?
            """,
            (now_iso, lead_id),
        )
        row = conn.execute(
            "SELECT channel, sender_id FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row:
            conn.execute(
                """
                INSERT INTO senders (channel, sender_id, owner_owned, bot_on)
                VALUES (?, ?, 1, 0)
                ON CONFLICT(channel, sender_id) DO UPDATE SET
                    owner_owned = 1,
                    bot_on = 0
                """,
                (row["channel"], row["sender_id"]),
            )


def is_owner_owned(channel: str, sender_id: str) -> bool:
    """Check if owner has taken over the thread and bot is paused."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT owner_owned, bot_on FROM senders WHERE channel = ? AND sender_id = ?",
            (channel, sender_id),
        ).fetchone()
        if row:
            return bool(row["owner_owned"]) and not bool(row["bot_on"])

        lead_row = conn.execute(
            """
            SELECT owner_took_over_at, bot_on FROM leads
            WHERE channel = ? AND sender_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (channel, sender_id),
        ).fetchone()
        if lead_row:
            return bool(lead_row["owner_took_over_at"]) and not bool(lead_row["bot_on"])
        return False


def set_bot_status(lead_id: int, bot_on: bool) -> None:
    """Enable or disable bot replies for a lead."""
    bot_val = 1 if bot_on else 0
    with _connect() as conn:
        conn.execute(
            "UPDATE leads SET bot_on = ? WHERE id = ?",
            (bot_val, lead_id),
        )
        row = conn.execute(
            "SELECT channel, sender_id FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row:
            conn.execute(
                """
                INSERT INTO senders (channel, sender_id, bot_on, owner_owned)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(channel, sender_id) DO UPDATE SET
                    bot_on = excluded.bot_on,
                    owner_owned = CASE WHEN excluded.bot_on = 1 THEN 0 ELSE senders.owner_owned END
                """,
                (row["channel"], row["sender_id"], bot_val, 0 if bot_on else 1),
            )


def has_auto_replied_in_24h(channel: str, sender_id: str) -> bool:
    """Check if an automated reply was sent to this sender within 24 hours."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_auto_reply_at FROM senders WHERE channel = ? AND sender_id = ?",
            (channel, sender_id),
        ).fetchone()

        last_str = row["last_auto_reply_at"] if row else None
        if not last_str:
            lead_row = conn.execute(
                """
                SELECT last_auto_reply_at FROM leads
                WHERE channel = ? AND sender_id = ? AND auto_reply_sent = 1
                ORDER BY id DESC LIMIT 1
                """,
                (channel, sender_id),
            ).fetchone()
            if lead_row:
                last_str = lead_row["last_auto_reply_at"]

        if not last_str:
            return False

        try:
            last_dt = datetime.fromisoformat(last_str)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - last_dt).total_seconds() < 86400
        except Exception:
            return False


def get_lead(lead_id: int) -> Optional[dict[str, Any]]:
    """Fetch lead by primary key."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None


def all_leads() -> list[dict[str, Any]]:
    """Return all leads ordered newest first."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def leads_as_csv() -> str:
    """Export all leads as a formatted CSV string."""
    rows = all_leads()
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
