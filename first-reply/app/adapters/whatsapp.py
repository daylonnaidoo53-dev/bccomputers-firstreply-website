"""
app/adapters/whatsapp.py — WhatsApp Cloud API adapter with fail-closed security.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from app.adapters.base import BaseAdapter, InboundMessage

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


class WhatsAppAdapter(BaseAdapter):
    """WhatsApp Cloud API integration adapter."""

    channel = "whatsapp"

    def verify_signature(
        self,
        raw_body: bytes,
        signature_header: str,
        app_secret: str,
    ) -> bool:
        """
        Verify incoming webhook signature (HMAC-SHA256).
        CRITICAL: Fails closed. If app_secret is missing, logs error and returns False.
        """
        if not app_secret:
            logger.error(
                "[whatsapp] WHATSAPP_APP_SECRET is not configured — rejecting signature (fail-closed)"
            )
            return False

        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("[whatsapp] Missing or invalid signature prefix")
            return False

        expected = hmac.new(
            app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        provided = signature_header[len("sha256=") :]
        return hmac.compare_digest(expected, provided)

    def normalize(self, raw: Any) -> Optional[InboundMessage]:
        """Parse Meta Cloud API message payload."""
        if not isinstance(raw, dict):
            return None

        try:
            entry = raw["entry"][0]
            change = entry["changes"][0]["value"]
            message = change["messages"][0]

            if message.get("type") != "text":
                return None

            sender_id = str(message["from"]).strip()
            contacts = change.get("contacts", [])
            sender_name = contacts[0]["profile"]["name"] if contacts else ""

            text = str(message["text"]["body"]).strip()
            ts = int(message.get("timestamp", 0))
            received_at = (
                datetime.fromtimestamp(ts, tz=timezone.utc)
                if ts
                else datetime.now(timezone.utc)
            )

            return InboundMessage(
                channel=self.channel,
                sender_id=sender_id,
                sender_name=sender_name,
                text=text,
                received_at=received_at,
            )
        except (KeyError, IndexError, TypeError):
            return None

    async def send(self, to: str, text: str, cfg: Config) -> None:
        """Send message via Meta WhatsApp Cloud API."""
        if not cfg.whatsapp_access_token or not cfg.whatsapp_phone_number_id:
            logger.info(
                "[whatsapp] Cloud API credentials not configured. Would send to %s: %s",
                to,
                text,
            )
            return

        import httpx

        url = f"https://graph.facebook.com/v19.0/{cfg.whatsapp_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {cfg.whatsapp_access_token}"},
            )
            resp.raise_for_status()
        logger.info("[whatsapp] Message delivered to %s", to)
