"""
templates.py — Deterministic Offline Reply Engine for FirstReply PC.
Guarantees fast, high-quality first replies when offline or quotas are exhausted.
Zero network calls, zero external dependencies, 100% free and instant.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import re
from typing import Dict, Optional


class OfflineTemplateEngine:
    """Builds deterministic, high-conversion first replies based on tone and intent."""

    INTENT_KEYWORDS = {
        "booking": ["book", "booking", "schedule", "appointment", "slot", "when", "time", "trial", "visit"],
        "pricing": ["price", "cost", "how much", "rate", "fee", "package", "quote", "pricing", "afford"],
        "beginner": ["beginner", "start", "new", "never tried", "experience", "first time", "intro"],
        "support": ["help", "issue", "problem", "broken", "error", "not working", "fix", "repair", "assist"],
    }

    @classmethod
    def detect_intent(cls, message: str) -> str:
        """Categorize message intent based on key vocabulary."""
        text_lower = message.lower()
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in keywords):
                return intent
        return "general"

    @classmethod
    def generate(
        cls,
        message: str,
        tone: str = "casual",
        user_name: str = "Daylon Naidoo",
        business_name: str = "BCComputers / Local Studio",
    ) -> str:
        """Generate a contextual offline first reply tailored to tone and intent."""
        intent = cls.detect_intent(message)
        tone_normalized = (tone or "casual").lower().strip()

        # ── Casual & Friendly ─────────────────────────────────────────────────
        if tone_normalized in ("casual", "whatsapp"):
            if intent == "booking":
                return (
                    f"Hey! Thanks so much for reaching out to {business_name}.\n\n"
                    "We'd love to get you booked in! We usually have slots open during the week (mornings & evenings). "
                    "Which day and time generally works best for your schedule?\n\n"
                    f"— {user_name}"
                )
            elif intent == "pricing":
                return (
                    f"Hi there! Thanks for asking about our options at {business_name}.\n\n"
                    "We have flexible options depending on what you're looking to achieve. "
                    "Could you share a quick note on your specific goals so I can recommend the exact right fit?\n\n"
                    f"— {user_name}"
                )
            elif intent == "beginner":
                return (
                    f"Hey! So glad you reached out. Yes, we are 100% beginner-friendly!\n\n"
                    "Everyone starts somewhere and we walk you through everything step-by-step. "
                    "Would you like to come in for a quick intro session to see how it feels?\n\n"
                    f"— {user_name}"
                )
            elif intent == "support":
                return (
                    f"Hey! Thanks for flagging this. I've noted your message and am looking into it right now.\n\n"
                    "I'll follow up shortly with a solution once I've reviewed the details.\n\n"
                    f"— {user_name}"
                )
            else:
                return (
                    f"Hey! Thanks for getting in touch with {business_name}.\n\n"
                    "I got your message and will review it in just a moment. "
                    "Is there anything specific you need answered right away?\n\n"
                    f"— {user_name}"
                )

        # ── Professional & Crisp ──────────────────────────────────────────────
        elif tone_normalized in ("professional", "business", "formal"):
            if intent == "booking":
                return (
                    f"Good day,\n\nThank you for contacting {business_name}. "
                    "We would be delighted to schedule an appointment with you. "
                    "Please let us know your preferred date and time, and we will confirm availability promptly.\n\n"
                    f"Kind regards,\n{user_name}\n{business_name}"
                )
            elif intent == "pricing":
                return (
                    f"Good day,\n\nThank you for your interest in our services at {business_name}. "
                    "Our pricing is structured around your specific requirements. "
                    "Could you briefly outline your scope so we can provide an accurate quotation?\n\n"
                    f"Kind regards,\n{user_name}\n{business_name}"
                )
            else:
                return (
                    f"Good day,\n\nThank you for reaching out to {business_name}. "
                    "Your enquiry has been received and is being attended to. "
                    "A member of our team will follow up with full details shortly.\n\n"
                    f"Kind regards,\n{user_name}\n{business_name}"
                )

        # ── Direct & Concise ──────────────────────────────────────────────────
        elif tone_normalized in ("direct", "concise"):
            if intent == "booking":
                return "Got your message. What day and time works best for you to get scheduled?"
            elif intent == "pricing":
                return "Thanks for reaching out. What specific package or outcome are you looking for?"
            elif intent == "support":
                return "Message received. Reviewing this now and will follow up with a fix shortly."
            else:
                return f"Thanks for contacting {business_name}. Reviewing your request now—what is your main priority?"

        # ── Empathetic & Warm ──────────────────────────────────────────────────
        elif tone_normalized in ("empathetic", "warm"):
            return (
                f"Hi there! Thank you so much for taking the time to write to us at {business_name}.\n\n"
                "We really appreciate you getting in touch. Whatever your questions or goals are, "
                "we're here to help make things easy and stress-free for you. "
                "Tell us a bit more about what you're hoping for, and we'll take care of the rest!\n\n"
                f"Warmly,\n{user_name}"
            )

        # ── Urgent Booking / Conversion ───────────────────────────────────────
        elif tone_normalized in ("urgent_booking", "booking"):
            return (
                f"Hi! Thanks for reaching out to {business_name}.\n\n"
                "We currently have opening slots available this week. "
                "Let us know which time suits you best, and we will lock in your spot right away:\n"
                "  • Mon 6:00am\n"
                "  • Wed 6:00pm\n"
                "  • Sat 8:00am\n\n"
                "Which one works for you?\n\n"
                f"— {user_name}"
            )

        # Fallback
        return (
            f"Hi! Thanks for contacting {business_name}.\n\n"
            "We received your message and will get back to you with all the details shortly. "
            "How can we best help you today?\n\n"
            f"— {user_name}"
        )
