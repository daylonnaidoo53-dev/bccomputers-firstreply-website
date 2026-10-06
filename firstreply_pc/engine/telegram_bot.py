"""
telegram_bot.py — Zero-Config Automated Telegram Assistant for FirstReply PC.
Acts as the official AI customer representative for the business.
Uses native HTTP long-polling (no port forwarding, no webhooks, 100% free forever).
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from firstreply_pc.engine import database
from firstreply_pc.engine.router import ModelRouter

logger = logging.getLogger(__name__)


class TelegramBotRunner:
    """Manages the lifecycle and message dispatch of the Telegram Customer Bot."""

    def __init__(self, router: Optional[ModelRouter] = None):
        self.router = router or ModelRouter()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_offset = 0

    def get_token(self) -> str:
        settings = database.get_all_settings()
        return settings.get("telegram_bot_token", "").strip()

    async def verify_bot(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Test if the provided Telegram Bot Token is valid."""
        tok = token or self.get_token()
        if not tok:
            return {"valid": False, "error": "No Telegram bot token configured"}

        url = f"https://api.telegram.org/bot{tok}/getMe"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                data = res.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    return {
                        "valid": True,
                        "username": bot_info.get("username"),
                        "first_name": bot_info.get("first_name"),
                        "can_join_groups": bot_info.get("can_join_groups"),
                    }
                return {"valid": False, "error": data.get("description", "Invalid token")}
        except Exception as exc:
            return {"valid": False, "error": str(exc)}

    async def send_message(self, chat_id: int | str, text: str, token: Optional[str] = None) -> bool:
        """Send a message to a specific Telegram chat."""
        tok = token or self.get_token()
        if not tok:
            return False

        url = f"https://api.telegram.org/bot{tok}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if not res.json().get("ok"):
                    # Fallback without HTML formatting if markdown parsing fails
                    payload.pop("parse_mode", None)
                    await client.post(url, json=payload)
                return True
        except Exception as exc:
            logger.error(f"[Telegram] Failed to send message to {chat_id}: {exc}")
            return False

    async def send_typing_action(self, chat_id: int | str, token: Optional[str] = None) -> None:
        """Show 'typing...' indicator while LLM generates."""
        tok = token or self.get_token()
        if not tok:
            return
        url = f"https://api.telegram.org/bot{tok}/sendChatAction"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(url, json={"chat_id": chat_id, "action": "typing"})
        except Exception:
            pass

    async def start(self) -> Dict[str, Any]:
        """Start background polling loop."""
        if self.is_running:
            return {"status": "already_running"}

        token = self.get_token()
        if not token:
            return {"status": "error", "error": "Telegram Bot Token is missing. Add it in Settings or .env"}

        check = await self.verify_bot(token)
        if not check.get("valid"):
            return {"status": "error", "error": f"Invalid bot token: {check.get('error')}"}

        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"[Telegram] Started bot listener for @{check.get('username')}")
        return {"status": "running", "bot": check}

    async def stop(self) -> Dict[str, Any]:
        """Stop background polling loop."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("[Telegram] Bot listener stopped.")
        return {"status": "stopped"}

    async def _poll_loop(self) -> None:
        """Continuous long-polling loop."""
        logger.info("[Telegram] Polling loop initialized.")
        while self.is_running:
            token = self.get_token()
            if not token:
                logger.warning("[Telegram] Token disappeared, pausing poll.")
                await asyncio.sleep(5)
                continue

            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {
                "offset": self._last_offset,
                "timeout": 20,
                "allowed_updates": ["message"],
            }

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        updates = data.get("result", [])
                        for update in updates:
                            self._last_offset = update["update_id"] + 1
                            if "message" in update and "text" in update["message"]:
                                # Process message asynchronously
                                asyncio.create_task(self._handle_incoming_message(update["message"], token))
                    elif res.status_code == 409:
                        # Conflict (another instance polling)
                        logger.warning("[Telegram] 409 Conflict: Another instance is polling this token. Waiting 10s...")
                        await asyncio.sleep(10)
                    else:
                        await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[Telegram] Polling error: {exc}")
                await asyncio.sleep(3)

    async def _handle_incoming_message(self, message: Dict[str, Any], token: str) -> None:
        """Route customer text to the FirstReply LLM engine and send back the company response."""
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        from_user = message.get("from", {})
        sender_name = from_user.get("first_name") or from_user.get("username") or "Customer"

        if not text:
            return

        settings = database.get_all_settings()
        business_name = settings.get("business_name", "BC Computers")

        # Handle commands
        if text.startswith("/start"):
            welcome = (
                f"Hello! Welcome to <b>{business_name}</b> in Paarl.\n\n"
                "I'm the BC Computers assistant. We provide managed IT, cloud management, IT support, and the First-Reply System. A team member will follow up personally. How can we help you? 👋"
            )
            await self.send_message(chat_id, welcome, token)
            return

        if text.startswith("/help"):
            help_txt = (
                f"ℹ️ <b>{business_name} Assistant</b>\n\n"
                "Ask about our managed IT, cloud management, IT support, or First-Reply System, and a team member will follow up with you personally."
            )
            await self.send_message(chat_id, help_txt, token)
            return

        # Show typing indicator
        await self.send_typing_action(chat_id, token)

        # Generate company response via FirstReply router
        try:
            tone = settings.get("telegram_bot_tone", "casual")
            result = await self.router.generate_reply(
                inbound_text=f"Customer ({sender_name}) asked: {text}",
                tone_slug=tone,
                channel="telegram",
            )
            reply_text = result.get("reply", "").strip()
            if not reply_text:
                reply_text = f"Thanks for reaching out to {business_name}! We received your message and will follow up with you shortly."

            # Send back to Telegram
            await self.send_message(chat_id, reply_text, token)
            logger.info(f"[Telegram] Replied to {sender_name} (chat {chat_id}) via {result.get('provider')} / {result.get('model')}")

        except Exception as exc:
            logger.error(f"[Telegram] Failed to generate automated reply: {exc}")
            fallback = f"Thanks for reaching out to {business_name}! We're reviewing your note and will be in touch in just a moment."
            await self.send_message(chat_id, fallback, token)


# Global singleton instance
telegram_runner = TelegramBotRunner()
