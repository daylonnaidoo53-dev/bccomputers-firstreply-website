"""
tests/test_handoff.py — Human handoff and suppression of duplicate auto-replies.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import time

import database as db

SENDER = "handoff_sender@example.com"


def test_second_message_forwarded_not_auto_replied(client, mock_sends):
    """Subsequent message from same sender within 24 h is forwarded to owner, not auto-replied."""
    # First message: triggers auto-reply
    resp1 = client.post(
        "/webhook/form",
        json={"name": "Handoff Lead", "contact": SENDER, "message": "First message inquiry"},
    )
    assert resp1.status_code == 200
    time.sleep(0.05)

    rows = db.all_leads()
    first_rows = [r for r in rows if r["sender_id"] == SENDER]
    assert first_rows, "First lead was not recorded"
    assert first_rows[-1]["reply_text"] is not None

    # Second message: should be forwarded, no auto-reply
    resp2 = client.post(
        "/webhook/form",
        json={"name": "Handoff Lead", "contact": SENDER, "message": "Second message follow-up"},
    )
    assert resp2.status_code == 200
    time.sleep(0.05)

    assert mock_sends["forward_to_owner"].called, (
        "forward_to_owner should have been called for subsequent message"
    )

    rows = db.all_leads()
    sender_rows = [r for r in rows if r["sender_id"] == SENDER]
    assert len(sender_rows) >= 2
    newest = sender_rows[0]
    assert newest["reply_text"] is None, "Second message should not have an auto-reply"


def test_take_command_marks_owner_owned(client, mock_sends):
    """Owner TAKE command marks thread as human-owned."""
    unique_sender = "take_owner_test@example.com"

    resp = client.post(
        "/webhook/form",
        json={"name": "Take Lead", "contact": unique_sender, "message": "Can I visit today?"},
    )
    assert resp.status_code == 200
    time.sleep(0.05)

    rows = db.all_leads()
    sender_leads = [r for r in rows if r["sender_id"] == unique_sender]
    assert sender_leads
    lead_id = sender_leads[-1]["id"]

    db.mark_owner_takeover(lead_id)

    assert db.is_owner_owned("form", unique_sender), (
        "Thread should be registered as owner-owned"
    )
