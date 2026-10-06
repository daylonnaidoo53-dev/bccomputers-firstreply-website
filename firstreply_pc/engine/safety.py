"""
safety.py — Safety filter and anti-hallucination layer for FirstReply PC.
Ensures replies are safe, free of PII leaks, and grounded in approved facts.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import re
from typing import List, Set, Tuple


class SafetyFilter:
    """Validates generated text and incoming prompts for safety and truthfulness."""

    # Patterns for potential PII or prompt injections
    CC_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|above)\s+instructions?", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(DAN|unrestricted|god\s+mode)", re.IGNORECASE),
        re.compile(r"system\s*:\s*system\s+prompt", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize incoming text against prompt injection or exploit vectors."""
        sanitized = text
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub("[REDACTED PROMPT OVERRIDE ATTEMPT]", sanitized)
        # Redact payment card numbers from prompt
        sanitized = cls.CC_PATTERN.sub("[REDACTED PAYMENT DATA]", sanitized)
        return sanitized

    @classmethod
    def validate_reply(
        cls,
        reply_text: str,
        allowed_numbers: Set[str],
        allowed_urls: Set[str],
    ) -> Tuple[bool, List[str]]:
        """
        Validate generated reply against fact whitelists.
        Rejects rogue prices, unapproved phone numbers, or unknown links.
        """
        errors: List[str] = []

        # 1. URL Check
        found_urls = re.findall(r"https?://\S+", reply_text)
        for raw_url in found_urls:
            url = raw_url.rstrip("!.,;:?)\"'>")
            if url not in allowed_urls:
                errors.append(f"Unapproved URL found in reply: {url}")

        # 2. Number / Price Check
        # Allow common times (e.g., 2, 5, 24, 7, 0) and small numbers if not a currency price
        found_numbers = set(re.findall(r"\d+", reply_text))
        suspicious_numbers = found_numbers - allowed_numbers - {"1", "2", "3", "5", "10", "24", "48"}
        
        # Check specifically for currency symbols like R, $, €, £
        price_matches = re.findall(r"(?:R|\$|€|£)\s*\d+", reply_text)
        if price_matches:
            # If any currency appears and wasn't explicitly permitted, flag it
            for pm in price_matches:
                clean_digits = "".join(re.findall(r"\d+", pm))
                if clean_digits not in allowed_numbers:
                    errors.append(f"Unapproved price quote detected: {pm}")

        if suspicious_numbers:
            # Check if any large digits represent phone or bank info
            large_digits = [n for n in suspicious_numbers if len(n) >= 5]
            if large_digits:
                errors.append(f"Unapproved large number detected: {', '.join(large_digits)}")

        is_valid = len(errors) == 0
        return is_valid, errors

    @classmethod
    def clean_model_output(cls, text: str) -> str:
        """Strip internal reasoning tags, meta-thought traces, or leading preamble."""
        clean = text.strip()
        # Remove <think>...</think> blocks
        clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.DOTALL).strip()
        
        # If output contains "Let's craft: "..." or "Let's draft: "...", extract the draft
        draft_match = re.search(r"(?:Let's\s+(?:draft|craft|say)|Draft|Craft|Here is a draft|Reply):\s*[\"“](.*?)(?:[\"”\n]|$)", clean, flags=re.DOTALL | re.IGNORECASE)
        if draft_match:
            extracted = draft_match.group(1).strip()
            if len(extracted) > 10:
                clean = extracted
        else:
            # Check for multi-paragraph reasoning followed by final response
            parts = clean.split("\n\n")
            if len(parts) > 1 and ("we need to" in parts[0].lower() or "the user is" in parts[0].lower() or "i should" in parts[0].lower()):
                # Filter out obvious thought paragraphs
                actual_parts = [p for p in parts if not (p.lower().startswith("we need") or p.lower().startswith("i need") or p.lower().startswith("the user wants") or p.lower().startswith("check length"))]
                if actual_parts:
                    clean = "\n\n".join(actual_parts).strip()

        # Remove surrounding wrapping quotes if entire text is in quotes
        if (clean.startswith('"') and clean.endswith('"')) or (clean.startswith('“') and clean.endswith('”')):
            clean = clean[1:-1].strip()

        return clean
