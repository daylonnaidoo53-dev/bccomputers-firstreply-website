"""
tests/test_sla.py — SLA compliance testing.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import datetime
import time

import database as db


def test_replied_within_sla(client):
    """A standard form lead should be recorded as replied within SLA."""
    resp = client.post(
        "/webhook/form",
        json={"name": "SLA User", "contact": "sla_user@example.com", "message": "Interested in joining"},
    )
    assert resp.status_code == 200
    time.sleep(0.05)

    rows = db.all_leads()
    assert rows, "Lead record not inserted"
    latest = rows[0]
    assert latest["reply_text"] is not None
    assert latest["reply_sent_at"] is not None
    assert latest["replied_within_sla"] == 1


def test_sla_flag_false_when_slow(client, monkeypatch):
    """When processing is delayed past SLA window, replied_within_sla should be 0."""
    from app.routes import webhooks as wh

    original_handle = wh._handle_message

    async def slow_handle(msg):
        # Backdate received_at by 5 minutes to simulate breach
        backdated = msg.__class__(
            channel=msg.channel,
            sender_id="slow_sla_sender@example.com",
            sender_name=msg.sender_name,
            text=msg.text,
            received_at=msg.received_at - datetime.timedelta(minutes=5),
        )
        return await original_handle(backdated)

    monkeypatch.setattr(wh, "_handle_message", slow_handle)

    resp = client.post(
        "/webhook/form",
        json={"name": "Slow Lead", "contact": "slow_sla_sender@example.com", "message": "hello"},
    )
    assert resp.status_code == 200
    time.sleep(0.05)

    rows = db.all_leads()
    slow_rows = [r for r in rows if r["sender_id"] == "slow_sla_sender@example.com"]
    assert slow_rows
    assert slow_rows[0]["replied_within_sla"] == 0
