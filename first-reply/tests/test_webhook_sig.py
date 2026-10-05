"""
tests/test_webhook_sig.py — WhatsApp webhook signature verification & handshake.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import hashlib
import hmac
import json

APP_SECRET = "test-secret"

WA_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "messages": [
                            {
                                "from": "27821234567",
                                "type": "text",
                                "timestamp": "1700000000",
                                "text": {"body": "Hello!"},
                            }
                        ],
                        "contacts": [{"profile": {"name": "Test User"}}],
                    }
                }
            ]
        }
    ]
}


def _make_sig(body: bytes, secret: str = APP_SECRET) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature_accepted(client):
    body = json.dumps(WA_PAYLOAD).encode("utf-8")
    sig = _make_sig(body)

    resp = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
        },
    )
    assert resp.status_code == 200


def test_wrong_signature_rejected(client):
    body = json.dumps(WA_PAYLOAD).encode("utf-8")
    bad_sig = _make_sig(body, secret="wrong-secret")

    resp = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": bad_sig,
        },
    )
    assert resp.status_code == 403


def test_missing_signature_rejected(client):
    body = json.dumps(WA_PAYLOAD).encode("utf-8")

    resp = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 403


def test_verify_handshake_success(client):
    resp = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify",
            "hub.challenge": "abc12345",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "abc12345"


def test_verify_handshake_wrong_token(client):
    resp = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "abc12345",
        },
    )
    assert resp.status_code == 403
