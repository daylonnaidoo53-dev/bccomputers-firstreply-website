"""
reply.py — Deterministic first-reply template and LLM safety validator.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


def build_reply(name: str, cfg: Config) -> str:
    """Build deterministic first-reply text using only configured facts."""
    clean_name = (name or "").strip()
    greeting = f"Hi {clean_name}," if clean_name else "Hi there,"

    if cfg.booking_link:
        body = (
            f"thanks for reaching out to {cfg.business_name} in {cfg.city}!\n\n"
            f"We'd love to offer you a {cfg.offer_name}. "
            f"You can book a time that suits you here: {cfg.booking_link}\n\n"
            "Which slot works best for you?"
        )
    else:
        slots = "\n".join(f"  • {slot}" for slot in cfg.trial_slots)
        body = (
            f"thanks for reaching out to {cfg.business_name} in {cfg.city}!\n\n"
            f"We'd love to offer you a {cfg.offer_name}. "
            f"We have the following slots available:\n\n{slots}\n\n"
            "Which one suits you?"
        )

    footer = (
        "\nJust reply with your preferred time and we'll get you sorted. "
        "A team member will follow up shortly.\n\n"
        f"— {cfg.business_name}"
    )

    return f"{greeting} {body}{footer}"


def _validate_llm_output(text: str, cfg: Config) -> bool:
    """
    Validate LLM output against strict whitelist rules.
    Rejects any unapproved numbers, prices, or URLs.
    """
    # Allowed numbers strictly from config
    allowed_numbers: set[str] = set()
    for slot in cfg.trial_slots:
        allowed_numbers.update(re.findall(r"\d+", slot))
    if cfg.owner_whatsapp:
        allowed_numbers.update(re.findall(r"\d+", cfg.owner_whatsapp))
    if cfg.booking_link:
        allowed_numbers.update(re.findall(r"\d+", cfg.booking_link))

    for num in re.findall(r"\d+", text):
        if num not in allowed_numbers:
            return False

    # Allowed URLs strictly matching booking_link
    found_urls = re.findall(r"https?://\S+", text)
    for raw_url in found_urls:
        url = raw_url.rstrip("!.,;:?)\"'>")
        if not cfg.booking_link or url != cfg.booking_link:
            return False

    return True


async def polish_reply(template: str, cfg: Config) -> str:
    """Optionally rephrase template using LLM while enforcing strict fact checking."""
    if not cfg.llm_polish or not cfg.openai_api_key:
        return template

    try:
        import httpx

        prompt = (
            "Rephrase the following business reply to sound warm, helpful, and concise. "
            "Do NOT add any new facts, numbers, prices, or URLs. "
            "Return only the rephrased message text.\n\n"
            f"---\n{template}\n---"
        )

        headers = {"Authorization": f"Bearer {cfg.openai_api_key}"}
        payload = {
            "model": cfg.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{cfg.openai_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            candidate = data["choices"][0]["message"]["content"].strip()

        if _validate_llm_output(candidate, cfg):
            return candidate

        logger.warning("[reply] Polished output failed fact validation; falling back to template")
        return template
    except Exception as exc:
        logger.warning("[reply] LLM polish failed (%r); falling back to template", exc)
        return template
