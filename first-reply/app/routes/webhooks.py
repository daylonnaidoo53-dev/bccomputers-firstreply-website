"""
app/routes/webhooks.py — Inbound webhook endpoints for all channels.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

import config
import database as db
from app import handoff
from app.adapters.form import FormAdapter
from app.adapters.whatsapp import WhatsAppAdapter
from app.adapters.base import InboundMessage
from reply import build_reply, polish_reply

logger = logging.getLogger(__name__)
router = APIRouter()

_ADAPTERS: dict[str, Any] = {
    "form": FormAdapter(),
    "whatsapp": WhatsAppAdapter(),
}

_STOP_PHRASES = ["stop", "opt out", "optout", "opt-out", "unsubscribe", "cancel"]


async def _handle_message(msg: InboundMessage) -> dict[str, Any]:
    """Run full first-reply pipeline for an inbound message."""
    cfg = config.cfg
    channel = msg.channel
    sender_id = msg.sender_id
    text_raw = msg.text.strip()
    text_lower = text_raw.lower()

    # 1. Opt-out check
    if any(phrase in text_lower for phrase in _STOP_PHRASES):
        db.mark_opted_out(channel, sender_id)
        logger.info("[pipeline] Opt-out triggered for %s on %s", sender_id, channel)
        return {"status": "opted_out"}

    if db.is_opted_out(channel, sender_id):
        logger.info("[pipeline] Dropping message from opted-out sender %s", sender_id)
        return {"status": "opted_out_drop"}

    # 2. Owner control commands
    upper_text = text_raw.upper()
    if upper_text.startswith("TAKE "):
        try:
            lead_id = int(upper_text.split()[1])
            db.mark_owner_takeover(lead_id)
            return {"status": "owner_command_take", "lead_id": lead_id}
        except (IndexError, ValueError):
            pass

    if upper_text.startswith("BOT ON "):
        try:
            lead_id = int(upper_text.split()[2])
            db.set_bot_status(lead_id, bot_on=True)
            return {"status": "owner_command_bot_on", "lead_id": lead_id}
        except (IndexError, ValueError):
            pass

    if upper_text.startswith("BOT OFF "):
        try:
            lead_id = int(upper_text.split()[2])
            db.set_bot_status(lead_id, bot_on=False)
            return {"status": "owner_command_bot_off", "lead_id": lead_id}
        except (IndexError, ValueError):
            pass

    # 3. Rate limit (24 h window) & owner takeover check
    already_replied = db.has_auto_replied_in_24h(channel, sender_id)
    owner_owns = db.is_owner_owned(channel, sender_id)

    if already_replied or owner_owns:
        lead_id = db.insert_lead(channel, sender_id, msg.sender_name, msg.text, msg.received_at)
        await handoff.forward_to_owner(cfg, lead_id, msg.sender_name, channel, msg.text)
        return {"status": "forwarded_to_owner", "lead_id": lead_id}

    # 4. First reply execution
    lead_id = db.insert_lead(channel, sender_id, msg.sender_name, msg.text, msg.received_at)
    reply_text = build_reply(msg.sender_name, cfg)
    reply_text = await polish_reply(reply_text, cfg)

    adapter = _ADAPTERS[channel]
    sent_at: datetime | None = None
    sent_ok = False

    for attempt in range(2):
        try:
            await adapter.send(sender_id, reply_text, cfg)
            sent_at = datetime.now(timezone.utc)
            sent_ok = True
            break
        except Exception as exc:
            logger.warning("[pipeline] Send attempt %d failed: %r", attempt + 1, exc)

    if not sent_ok:
        logger.error("[pipeline] Reply delivery failed for lead %d", lead_id)
        try:
            await handoff.notify_owner(
                cfg, lead_id, msg.sender_name, channel, msg.text, f"[SEND FAILED] {reply_text}"
            )
        except Exception:
            pass
    else:
        assert sent_at is not None
        sla_met = (sent_at - msg.received_at).total_seconds() <= cfg.sla_seconds
        db.update_reply(lead_id, reply_text, sent_at, sla_met)
        try:
            await handoff.notify_owner(
                cfg, lead_id, msg.sender_name, channel, msg.text, reply_text
            )
        except Exception as exc:
            logger.error("[pipeline] Owner notification error: %r", exc)

    return {
        "status": "replied" if sent_ok else "send_failed",
        "lead_id": lead_id,
        "reply": reply_text,
    }


@router.post("/webhook/form")
async def webhook_form(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Ingest website contact form leads."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    adapter = _ADAPTERS["form"]
    msg = adapter.normalize(body)
    if not msg:
        raise HTTPException(status_code=400, detail="name, contact, and message required")

    background_tasks.add_task(_handle_message, msg)
    return {"status": "received"}


@router.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request) -> Response:
    """Meta Cloud API webhook verification handshake."""
    cfg = config.cfg
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge", "")

    if mode == "subscribe" and token == cfg.whatsapp_verify_token and token != "":
        logger.info("[whatsapp] Webhook handshake succeeded")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("[whatsapp] Webhook handshake failed (token mismatch)")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Inbound WhatsApp message webhook (fails closed if signature or secret invalid)."""
    cfg = config.cfg
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")

    adapter: WhatsAppAdapter = _ADAPTERS["whatsapp"]
    if not adapter.verify_signature(raw_body, signature_header, cfg.whatsapp_app_secret):
        logger.error("[whatsapp] Webhook rejected: signature invalid or unconfigured")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    msg = adapter.normalize(payload)
    if not msg:
        return {"status": "ignored"}

    background_tasks.add_task(_handle_message, msg)
    return {"status": "received"}
