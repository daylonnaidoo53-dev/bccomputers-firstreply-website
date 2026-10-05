"""
app/adapters/email.py — Inbound email adapter stub.
Author: Daylon Naido · BCComputers

TODO: Complete this file to enable direct email-to-lead ingestion.

Steps to finish:
  1. Choose an inbound email parsing provider:
       - SendGrid Inbound Parse -> webhook POST to /webhook/email
       - Mailgun Receiving Route -> webhook POST to /webhook/email
       - Postmark Inbound Webhook -> webhook POST to /webhook/email
  2. Implement normalize() to parse the provider's multipart or JSON body:
       - sender_id = sender's email address
       - sender_name = display name
       - text = stripped clean message body
  3. Implement send() utilizing send_email() from app.adapters.email_util.
  4. Register "email": EmailAdapter() in app/routes/webhooks.py _ADAPTERS.
  5. Verify webhook signatures or shared authorization tokens for security.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from app.adapters.base import BaseAdapter, InboundMessage

if TYPE_CHECKING:
    from config import Config


class EmailAdapter(BaseAdapter):
    """Inbound email provider adapter stub."""

    channel = "email"

    def normalize(self, raw: Any) -> Optional[InboundMessage]:
        raise NotImplementedError("Email adapter not yet implemented")

    async def send(self, to: str, text: str, cfg: Config) -> None:
        raise NotImplementedError("Email adapter not yet implemented")
