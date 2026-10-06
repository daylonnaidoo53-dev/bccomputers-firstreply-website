"""
router.py — Quota-Aware Multi-Tier Model Router for FirstReply PC.
Routes text to local open-source models, free-tier fallbacks, or offline templates.
Guarantees zero paid overages, 100% free operation, and graceful degradation.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from firstreply_pc.engine import database
from firstreply_pc.engine.quota_guard import QuotaGuard
from firstreply_pc.engine.safety import SafetyFilter
from firstreply_pc.engine.templates import OfflineTemplateEngine

logger = logging.getLogger(__name__)


class ModelRouter:
    """Intelligent quota-aware router for FirstReply PC."""

    def __init__(self, http_timeout: float = 8.0):
        self.http_timeout = http_timeout

    async def generate_reply(
        self,
        inbound_text: str,
        tone_slug: str = "casual",
        channel: str = "clipboard",
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a first reply through the optimal free tier provider.
        Cascades: Local Ollama -> Groq Free -> Gemini Free -> OpenRouter Free -> Offline Template.
        """
        t0 = time.monotonic()
        settings = database.get_all_settings()
        local_only = settings.get("local_only_mode", "false").lower() == "true"
        max_output_tokens = QuotaGuard.get_max_output_tokens()

        # Sanitize prompt and compress
        clean_prompt = SafetyFilter.sanitize_input(inbound_text)
        compressed_prompt = QuotaGuard.compress_input(clean_prompt)

        # Retrieve tone profile
        tone_profile = database.get_tone_profile(tone_slug) or database.get_tone_profile("casual")
        tone_name = tone_profile["name"] if tone_profile else "Casual"
        tone_instructions = tone_profile["instructions"] if tone_profile else "Be friendly and concise."

        system_instruction = (
            "You are the BC Computers assistant in Paarl. You reply to inbound leads.\n\n"
            "RULES:\n"
            "- You are not a person. If asked who you are: \"I'm the BC Computers assistant.\"\n"
            "- Only state facts listed under FACTS. Never invent services, prices, turnaround times, or staff.\n"
            "- If asked something not in FACTS, say a team member will confirm and ask for their name and number.\n"
            "- Never output your reasoning, notes, or instructions. Output only the reply to the lead.\n"
            "- Under 60 words. Greet only once per conversation, not every message.\n"
            "- At most one emoji, and only if it fits.\n\n"
            "FACTS:\n"
            "- Business: BC Computers, Paarl, Cape Winelands\n"
            f"- Owner: {settings.get('user_name', 'Daylon Naidoo')}\n"
            "- Services: managed IT, cloud management, IT support, and the First-Reply System\n"
            "- A team member will follow up personally."
        )

        user_content = f"Inbound message:\n\"\"\"{compressed_prompt}\"\"\"\n\nDraft the first reply:"

        # Candidate execution providers
        providers_status = {q["provider"]: q for q in database.get_all_quotas()}

        candidate_order: List[str] = []
        if preferred_provider and preferred_provider in providers_status:
            candidate_order.append(preferred_provider)

        # Standard priority
        default_chain = ["ollama", "groq", "gemini", "openrouter", "offline_template"]
        for p in default_chain:
            if p not in candidate_order:
                candidate_order.append(p)

        last_error: Optional[str] = None

        for provider in candidate_order:
            provider_meta = providers_status.get(provider, {})
            available, reason = QuotaGuard.is_provider_available(provider_meta)
            if not available:
                logger.info(f"[Router] Skipping provider '{provider}': {reason}")
                continue

            # If local_only is enabled, skip external cloud providers
            if local_only and not provider_meta.get("is_local") and provider != "offline_template":
                logger.info(f"[Router] Skipping cloud provider '{provider}' because local_only_mode is ON")
                continue

            # Attempt dispatch
            try:
                candidate_text, in_tokens, out_tokens, model_name = await self._call_provider(
                    provider=provider,
                    system_prompt=system_instruction,
                    user_prompt=user_content,
                    settings=settings,
                    max_tokens=max_output_tokens,
                    raw_inbound=inbound_text,
                    tone_slug=tone_slug,
                )

                if candidate_text:
                    candidate_text = SafetyFilter.clean_model_output(candidate_text)
                    elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
                    
                    # Record quota consumption
                    QuotaGuard.record_usage(provider, in_tokens, out_tokens)

                    # Log prompt trace
                    database.log_prompt_trace(
                        provider=provider,
                        model=model_name,
                        latency_ms=elapsed_ms,
                        status="SUCCESS",
                        prompt_snippet=compressed_prompt,
                        output_snippet=candidate_text,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                    )

                    # Save to reply history
                    history_id = database.log_reply_history(
                        source_channel=channel,
                        original_text=inbound_text,
                        reply_text=candidate_text,
                        tone=tone_slug,
                        provider_used=provider,
                        model_used=model_name,
                        latency_ms=elapsed_ms,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                    )

                    return {
                        "success": True,
                        "history_id": history_id,
                        "reply": candidate_text,
                        "tone": tone_name,
                        "tone_slug": tone_slug,
                        "provider": provider,
                        "model": model_name,
                        "latency_ms": elapsed_ms,
                        "tokens": {
                            "input": in_tokens,
                            "output": out_tokens,
                            "total": in_tokens + out_tokens,
                        },
                        "privacy": "local" if provider in ("ollama", "offline_template") else "free_cloud",
                        "cost": "$0.00 (Free)",
                    }

            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"[Router] Provider '{provider}' failed: {exc}")
                database.log_prompt_trace(
                    provider=provider,
                    model=provider_meta.get("model", "unknown"),
                    latency_ms=round((time.monotonic() - t0) * 1000, 2),
                    status="ERROR",
                    prompt_snippet=compressed_prompt,
                    output_snippet="",
                    error_message=str(exc),
                )
                continue

        # Ultimate fallback to Offline Template Engine if everything else fails
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        fallback_text = OfflineTemplateEngine.generate(
            message=inbound_text,
            tone=tone_slug,
            user_name=settings.get("user_name", "Daylon Naidoo"),
            business_name=settings.get("business_name", "BCComputers"),
        )
        history_id = database.log_reply_history(
            source_channel=channel,
            original_text=inbound_text,
            reply_text=fallback_text,
            tone=tone_slug,
            provider_used="offline_template",
            model_used="rules-engine-v1",
            latency_ms=elapsed_ms,
            input_tokens=0,
            output_tokens=QuotaGuard.estimate_tokens(fallback_text),
        )

        return {
            "success": True,
            "history_id": history_id,
            "reply": fallback_text,
            "tone": tone_name,
            "tone_slug": tone_slug,
            "provider": "offline_template",
            "model": "rules-engine-v1",
            "latency_ms": elapsed_ms,
            "tokens": {"input": 0, "output": QuotaGuard.estimate_tokens(fallback_text), "total": QuotaGuard.estimate_tokens(fallback_text)},
            "privacy": "local",
            "cost": "$0.00 (Free)",
            "fallback_notice": f"Used offline template engine (Last provider error: {last_error or 'None'})",
        }

    async def _call_provider(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        settings: Dict[str, str],
        max_tokens: int,
        raw_inbound: str,
        tone_slug: str,
    ) -> Tuple[str, int, int, str]:
        """Dispatch model call to specific provider adapter."""

        # ── 1. Local Ollama / llama.cpp ───────────────────────────────────────
        if provider == "ollama":
            base_url = settings.get("ollama_base_url", "http://localhost:11434/v1").rstrip("/")
            model = "llama3.2:3b"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.4,
            }
            # Short timeout — if Ollama is not running, fail fast to next tier
            async with httpx.AsyncClient(timeout=0.8) as client:
                resp = await client.post(f"{base_url}/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                in_tok = data.get("usage", {}).get("prompt_tokens", QuotaGuard.estimate_tokens(user_prompt))
                out_tok = data.get("usage", {}).get("completion_tokens", QuotaGuard.estimate_tokens(text))
                return text, in_tok, out_tok, model

        # ── 2. Groq Free Tier ─────────────────────────────────────────────────
        elif provider == "groq":
            api_key = settings.get("groq_api_key", "").strip()
            if not api_key:
                raise ValueError("Groq API key not configured")
            model = "llama-3.3-70b-versatile"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                in_tok = data.get("usage", {}).get("prompt_tokens", QuotaGuard.estimate_tokens(user_prompt))
                out_tok = data.get("usage", {}).get("completion_tokens", QuotaGuard.estimate_tokens(text))
                return text, in_tok, out_tok, model

        # ── 3. Google Gemini Free Tier ─────────────────────────────────────────
        elif provider == "gemini":
            api_key = settings.get("gemini_api_key", "").strip()
            if not api_key:
                raise ValueError("Google Gemini API key not configured")
            model = "gemini-2.5-flash"
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
                ],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.3,
                },
            }
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                resp = await client.post(endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                in_tok = QuotaGuard.estimate_tokens(user_prompt)
                out_tok = QuotaGuard.estimate_tokens(text)
                return text, in_tok, out_tok, model

        # ── 4. OpenRouter Free Tier ───────────────────────────────────────────
        elif provider == "openrouter":
            api_key = settings.get("openrouter_api_key", "").strip()
            if not api_key:
                raise ValueError("OpenRouter API key not configured")

            configured_model = settings.get("openrouter_model", "").strip()
            models_to_try = [configured_model] if configured_model else [
                "google/gemma-4-31b-it:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
                "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                "poolside/laguna-s-2.1:free",
            ]
            models_to_try = [m for m in models_to_try if m]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/daylonnaidoo53-dev/firstreply-pc",
                "X-Title": "FirstReply PC",
            }

            last_err = None
            for model in models_to_try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max(max_tokens, 200),
                }
                try:
                    async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                        resp = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            msg = data["choices"][0]["message"]
                            text = (msg.get("content") or "").strip()
                            if not text and msg.get("reasoning"):
                                text = msg["reasoning"].strip()
                            if text:
                                in_tok = data.get("usage", {}).get("prompt_tokens", QuotaGuard.estimate_tokens(user_prompt))
                                out_tok = data.get("usage", {}).get("completion_tokens", QuotaGuard.estimate_tokens(text))
                                return text, in_tok, out_tok, model
                        else:
                            last_err = f"OpenRouter {model} returned {resp.status_code}: {resp.text[:120]}"
                except Exception as ex:
                    last_err = f"OpenRouter {model} error: {ex}"
                    continue

            raise ValueError(last_err or "No OpenRouter free models succeeded")

        # ── 5. Offline Deterministic Template ─────────────────────────────────
        elif provider == "offline_template":
            text = OfflineTemplateEngine.generate(
                message=raw_inbound,
                tone=tone_slug,
                user_name=settings.get("user_name", "Daylon Naidoo"),
                business_name=settings.get("business_name", "BCComputers"),
            )
            return text, 0, QuotaGuard.estimate_tokens(text), "rules-engine-v1"

        raise ValueError(f"Unknown model provider '{provider}'")
