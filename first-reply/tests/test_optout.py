"""
tests/test_optout.py — Opt-out and stop word testing.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import time

import database as db


def test_stop_word_marks_opted_out(client):
    """Inbound STOP command upserts sender as opted out."""
    sender = "optout_stop_user@example.com"

    resp = client.post(
        "/webhook/form",
        json={"name": "Stop User", "contact": sender, "message": "STOP"},
    )
    assert resp.status_code == 200
    time.sleep(0.05)

    assert db.is_opted_out("form", sender), "Sender should be marked opted out"


def test_opted_out_message_dropped(client, mock_sends):
    """Messages from opted-out senders are dropped silently with no reply."""
    sender = "opted_out_dropped@example.com"
    db.mark_opted_out("form", sender)

    resp = client.post(
        "/webhook/form",
        json={"name": "Dropped Lead", "contact": sender, "message": "Are classes still running?"},
    )
    assert resp.status_code == 200
    time.sleep(0.05)

    assert not mock_sends["form_send"].called, "Form send should NOT fire for opted-out senders"


def test_opt_out_variants(client):
    """Test all valid stop word variations."""
    phrases = ["opt out", "OPT OUT", "Unsubscribe", "STOP please", "cancel"]
    for idx, phrase in enumerate(phrases):
        sender = f"variant_optout_{idx}@example.com"
        resp = client.post(
            "/webhook/form",
            json={"name": f"User {idx}", "contact": sender, "message": phrase},
        )
        assert resp.status_code == 200
        time.sleep(0.05)
        assert db.is_opted_out("form", sender), f"Phrase '{phrase}' should trigger opt-out"
