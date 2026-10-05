"""
app/adapters/form.py — Website contact form adapter.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from app.adapters.base import BaseAdapter, InboundMessage
from app.adapters.email_util import send_email

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


class FormAdapter(BaseAdapter):
    """Handles website contact form submissions."""

    channel = "form"

    def normalize(self, raw: Any) -> Optional[InboundMessage]:
        if not isinstance(raw, dict):
            return None

        sender_id = str(raw.get("contact", "")).strip()
        sender_name = str(raw.get("name", "")).strip()
        text = str(raw.get("message", "")).strip()

        if not text:
            return None

        return InboundMessage(
            channel=self.channel,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            received_at=datetime.now(timezone.utc),
        )

    async def send(self, to: str, text: str, cfg: Config) -> None:
        """Send auto-reply back to the lead's email address."""
        subject = f"Your enquiry at {cfg.business_name}"
        await send_email(to_email=to, subject=subject, body=text, cfg=cfg)
