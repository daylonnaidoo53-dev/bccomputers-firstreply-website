"""
app/adapters/email_util.py — Shared asynchronous SMTP helper.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import logging
from email.message import EmailMessage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    cfg: Config,
) -> None:
    """Send an email using configured SMTP settings."""
    if not cfg.smtp_host or not to_email:
        logger.info(
            "[email_util] SMTP not configured. Would send to %s: %s",
            to_email,
            subject,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.from_email or cfg.smtp_user
    msg["To"] = to_email
    msg.set_content(body)

    try:
        import aiosmtplib

        await aiosmtplib.send(
            msg,
            hostname=cfg.smtp_host,
            port=cfg.smtp_port,
            username=cfg.smtp_user or None,
            password=cfg.smtp_password or None,
            start_tls=cfg.smtp_use_tls,
            timeout=10,
        )
        logger.info("[email_util] Email delivered to %s", to_email)
    except Exception as exc:
        logger.error("[email_util] Failed sending email to %s: %r", to_email, exc)
        raise
