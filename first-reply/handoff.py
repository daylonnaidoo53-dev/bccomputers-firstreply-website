"""
handoff.py — Human handoff and owner notification logic.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


async def notify_owner(
    cfg: Config,
    lead_id: int,
    sender_name: str,
    channel: str,
    text: str,
    reply_text: str,
) -> None:
    """Notify the owner via WhatsApp and/or email about a new lead and the sent reply."""
    name_display = sender_name or "Unknown"
    summary = (
        f"[NEW LEAD #{lead_id}] [{channel.upper()}]\n"
        f"From: {name_display}\n"
        f"Message: {text}\n"
        f"Auto-Reply: {reply_text}"
    )
    logger.info("[handoff] Notification for owner: %s", summary)

    # In production, dispatch via WhatsApp Cloud API or SMTP if configured
    if cfg.owner_whatsapp and cfg.whatsapp_access_token and cfg.whatsapp_phone_number_id:
        try:
            import httpx

            url = f"https://graph.facebook.com/v19.0/{cfg.whatsapp_phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": cfg.owner_whatsapp,
                "type": "text",
                "text": {"body": summary},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {cfg.whatsapp_access_token}"},
                )
        except Exception as exc:
            logger.error("[handoff] WhatsApp notification error: %r", exc)


async def forward_to_owner(
    cfg: Config,
    lead_id: int,
    sender_name: str,
    channel: str,
    text: str,
) -> None:
    """Forward a subsequent lead message to the owner (auto-reply suppressed)."""
    name_display = sender_name or "Unknown"
    summary = (
        f"[FOLLOW-UP LEAD #{lead_id}] [{channel.upper()}]\n"
        f"From: {name_display}\n"
        f"Message: {text}\n"
        f"(Auto-reply withheld. Send 'BOT ON {lead_id}' to resume or reply directly to lead.)"
    )
    logger.info("[handoff] Forwarded to owner: %s", summary)

    if cfg.owner_whatsapp and cfg.whatsapp_access_token and cfg.whatsapp_phone_number_id:
        try:
            import httpx

            url = f"https://graph.facebook.com/v19.0/{cfg.whatsapp_phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": cfg.owner_whatsapp,
                "type": "text",
                "text": {"body": summary},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {cfg.whatsapp_access_token}"},
                )
        except Exception as exc:
            logger.error("[handoff] WhatsApp forwarding error: %r", exc)
