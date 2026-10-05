"""
tests/test_reply.py — First reply template and validator tests.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

from config import Config
from reply import _validate_llm_output, build_reply


def _test_cfg(**kwargs) -> Config:
    defaults = dict(
        business_name="Fitness Fuzion",
        city="Paarl",
        offer_name="free trial class",
        trial_slots=["Mon 6:00am", "Wed 6:00pm", "Sat 8:00am"],
        owner_whatsapp="+27824673870",
        owner_email="info@fitnessfuzion.co.za",
        booking_link="",
        llm_polish=False,
        sla_seconds=120,
    )
    defaults.update(kwargs)
    return Config(**defaults)


def test_contains_business_name():
    cfg = _test_cfg()
    reply = build_reply("Alice", cfg)
    assert "Fitness Fuzion" in reply


def test_contains_city():
    cfg = _test_cfg()
    reply = build_reply("Alice", cfg)
    assert "Paarl" in reply


def test_contains_offer_name():
    cfg = _test_cfg()
    reply = build_reply("Alice", cfg)
    assert "free trial class" in reply


def test_all_trial_slots_present():
    cfg = _test_cfg()
    reply = build_reply("Alice", cfg)
    for slot in cfg.trial_slots:
        assert slot in reply, f"Expected slot '{slot}' in reply"


def test_greets_by_name():
    cfg = _test_cfg()
    reply = build_reply("Sarah", cfg)
    assert "Sarah" in reply


def test_generic_greeting_without_name():
    cfg = _test_cfg()
    reply = build_reply("", cfg)
    assert "Hi there" in reply


def test_uses_booking_link_when_set():
    cfg = _test_cfg(booking_link="https://book.fitnessfuzion.co.za")
    reply = build_reply("Bob", cfg)
    assert "https://book.fitnessfuzion.co.za" in reply
    for slot in cfg.trial_slots:
        assert slot not in reply


def test_no_booking_link_shows_slots():
    cfg = _test_cfg(booking_link="")
    reply = build_reply("Bob", cfg)
    assert "Mon 6:00am" in reply


def test_rejects_invented_price():
    cfg = _test_cfg()
    bad = "Join us for R250 per month at Fitness Fuzion in Paarl!"
    assert not _validate_llm_output(bad, cfg)


def test_rejects_invented_url():
    cfg = _test_cfg()
    bad = "Book at https://evil.com/link now!"
    assert not _validate_llm_output(bad, cfg)


def test_accepts_clean_output():
    cfg = _test_cfg()
    good = "Hi there! Come join us at Fitness Fuzion in Paarl for a free trial class!"
    assert _validate_llm_output(good, cfg)


def test_accepts_slot_numbers():
    cfg = _test_cfg()
    good = "We have slots at Mon 6:00am, Wed 6:00pm, and Sat 8:00am."
    assert _validate_llm_output(good, cfg)
