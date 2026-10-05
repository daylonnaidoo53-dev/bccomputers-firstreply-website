"""
app/adapters/instagram.py — Instagram Messaging adapter stub.
Author: Daylon Naido · BCComputers

TODO: Complete this file to enable Instagram DM support.

Steps to finish:
  1. In your Meta App Dashboard, add the "Instagram" product and subscribe
     to the "messages" webhook field on your connected Instagram professional page.
  2. Implement normalize() to parse incoming Instagram webhook events (similar
     to WhatsApp but utilizing page-scoped IDs: IGSID).
  3. Implement send() using the Instagram Graph API:
       POST https://graph.facebook.com/v19.0/me/messages
       with JSON: { "recipient": {"id": <sender_id>}, "message": {"text": <text>} }
  4. Signature verification uses the same X-Hub-Signature-256 header as WhatsApp.
  5. Register "instagram": InstagramAdapter() in app/routes/webhooks.py _ADAPTERS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from app.adapters.base import BaseAdapter, InboundMessage

if TYPE_CHECKING:
    from config import Config


class InstagramAdapter(BaseAdapter):
    """Instagram Direct Messaging channel adapter stub."""

    channel = "instagram"

    def normalize(self, raw: Any) -> Optional[InboundMessage]:
        raise NotImplementedError("Instagram adapter not yet implemented")

    async def send(self, to: str, text: str, cfg: Config) -> None:
        raise NotImplementedError("Instagram adapter not yet implemented")
