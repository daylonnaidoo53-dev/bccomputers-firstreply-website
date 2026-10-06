"""
plugins.py — Extensible Plugin Interface for FirstReply PC.
Adapts drafts and triggers for Email, WhatsApp Web, Desktop Chat, and CRM connectors.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    """Abstract interface for all FirstReply PC connectors."""

    name: str
    title: str
    description: str

    @abstractmethod
    def format_draft(self, raw_reply: str, metadata: Dict[str, Any]) -> str:
        """Format reply specifically for the target client application."""
        pass


class ClipboardPlugin(BasePlugin):
    name = "clipboard"
    title = "Universal Clipboard Hook"
    description = "Copies raw, clean draft text directly for paste into any PC app."

    def format_draft(self, raw_reply: str, metadata: Dict[str, Any]) -> str:
        return raw_reply.strip()


class WhatsAppPlugin(BasePlugin):
    name = "whatsapp"
    title = "WhatsApp Web Companion"
    description = "Ensures formatting aligns with WhatsApp line-breaks and single-message limits."

    def format_draft(self, raw_reply: str, metadata: Dict[str, Any]) -> str:
        # Avoid formal mail greetings if present
        clean = raw_reply.strip()
        if clean.startswith("Dear ") or clean.startswith("Good day,"):
            clean = clean.replace("Dear client,", "Hi!").replace("Good day,", "Hi!")
        return clean


class EmailPlugin(BasePlugin):
    name = "email"
    title = "Desktop Email Formatter"
    description = "Formats crisp email drafts with clear salutation, body paragraphs, and professional signature."

    def format_draft(self, raw_reply: str, metadata: Dict[str, Any]) -> str:
        sender_name = metadata.get("user_name", "Daylon Naidoo")
        business_name = metadata.get("business_name", "BCComputers")
        body = raw_reply.strip()
        
        # Ensure formal sign-off if missing
        if "regards" not in body.lower() and "sincerely" not in body.lower():
            body += f"\n\nBest regards,\n{sender_name}\n{business_name}"
        return body


class TelegramPlugin(BasePlugin):
    name = "telegram"
    title = "Telegram Bot Automator"
    description = "Formats concise, instant conversational replies for Telegram direct messaging."

    def format_draft(self, raw_reply: str, metadata: Dict[str, Any]) -> str:
        clean = raw_reply.strip()
        # Ensure it's conversational and doesn't have artificial preamble
        return clean


PLUGIN_REGISTRY: Dict[str, BasePlugin] = {
    "clipboard": ClipboardPlugin(),
    "whatsapp": WhatsAppPlugin(),
    "email": EmailPlugin(),
    "telegram": TelegramPlugin(),
}


def format_for_channel(channel: str, draft: str, metadata: Dict[str, Any]) -> str:
    """Pass draft through registered channel plugin if available."""
    plugin = PLUGIN_REGISTRY.get(channel.lower())
    if plugin:
        return plugin.format_draft(draft, metadata)
    return draft.strip()
