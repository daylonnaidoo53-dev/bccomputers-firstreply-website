"""
quota_guard.py — Free AI Quota & Budget Enforcement for FirstReply PC.
Ensures zero-cost guarantee, tracks provider quotas, and enforces token ceilings.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple
from firstreply_pc.engine import database

logger = logging.getLogger(__name__)

# Default hard ceilings to keep within free allowances
DEFAULT_MAX_INPUT_CHARS = 1500     # ~350 tokens, prevents unbounded prompt blowout
DEFAULT_MAX_OUTPUT_TOKENS = 256    # Standard concise first reply limit
STOP_THRESHOLD_PERCENT = 0.95      # Stop using provider if 95% of daily free allowance is used


class QuotaGuard:
    """Manages provider quota consumption and prevents billing overage."""

    @staticmethod
    def is_provider_available(provider_row: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if provider has active quota remaining below safety threshold."""
        if not provider_row.get("is_active", 1):
            return False, "Provider is disabled in settings"

        # Local providers and offline templates have infinite free quota
        if provider_row.get("is_local") or provider_row.get("provider") in ("ollama", "offline_template"):
            return True, "Local / zero-cost unlimited"

        req_used = provider_row.get("daily_requests_used", 0)
        req_limit = provider_row.get("daily_requests_limit", 1000)
        tok_used = provider_row.get("daily_tokens_used", 0)
        tok_limit = provider_row.get("daily_tokens_limit", 500000)

        # Enforce 95% stop threshold
        if req_used >= (req_limit * STOP_THRESHOLD_PERCENT):
            return False, f"Daily request quota near limit ({req_used}/{req_limit})"

        if tok_used >= (tok_limit * STOP_THRESHOLD_PERCENT):
            return False, f"Daily token quota near limit ({tok_used}/{tok_limit})"

        return True, "Quota available"

    @staticmethod
    def compress_input(text: str, max_chars: int = DEFAULT_MAX_INPUT_CHARS) -> str:
        """
        Compress and sanitize input prompt text to minimize token consumption.
        - Trims excessive whitespace
        - Collapses repeated newlines
        - Safely cuts to max character boundary without splitting mid-sentence if possible.
        """
        cleaned = " ".join(text.strip().split())
        if len(cleaned) <= max_chars:
            return cleaned

        # Cut safely at word boundary
        truncated = cleaned[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + " ... [context truncated for quota efficiency]"

    @staticmethod
    def get_max_output_tokens() -> int:
        """Fetch configured max output tokens limit."""
        settings = database.get_all_settings()
        val = settings.get("max_output_tokens", str(DEFAULT_MAX_OUTPUT_TOKENS))
        try:
            return int(val)
        except ValueError:
            return DEFAULT_MAX_OUTPUT_TOKENS

    @staticmethod
    def record_usage(provider: str, input_tokens: int, output_tokens: int) -> None:
        """Record token consumption in database quota table."""
        total_tokens = input_tokens + output_tokens
        database.update_quota_consumption(provider, req_count=1, token_count=total_tokens)
        logger.info(
            f"[QuotaGuard] Recorded 1 request and {total_tokens} tokens for provider '{provider}'"
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Fast heuristic token estimator (~4 chars per token)."""
        return max(1, len(text) // 4)
