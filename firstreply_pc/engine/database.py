"""
database.py — SQLite storage for FirstReply PC.
Tracks reply history, quota usage, prompt traces, tone profiles, and settings.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE: Path | str = Path(__file__).resolve().parent.parent / "firstreply.db"
CURRENT_DB_PATH: Path | str = DB_FILE


def get_connection(custom_path: Optional[Path | str] = None) -> sqlite3.Connection:
    path = str(custom_path or CURRENT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(custom_path: Optional[Path | str] = None) -> None:
    """Initialize schema for FirstReply PC."""
    global CURRENT_DB_PATH
    if custom_path is not None:
        CURRENT_DB_PATH = custom_path

    with get_connection(CURRENT_DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel TEXT DEFAULT 'clipboard',
                original_text  TEXT NOT NULL,
                reply_text     TEXT NOT NULL,
                tone           TEXT NOT NULL,
                provider_used  TEXT NOT NULL,
                model_used     TEXT NOT NULL,
                latency_ms     REAL NOT NULL,
                input_tokens   INTEGER DEFAULT 0,
                output_tokens  INTEGER DEFAULT 0,
                approved       INTEGER DEFAULT 0,
                copied         INTEGER DEFAULT 0,
                created_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quotas (
                provider               TEXT PRIMARY KEY,
                display_name           TEXT NOT NULL,
                model                  TEXT NOT NULL,
                is_local               INTEGER DEFAULT 0,
                daily_requests_used    INTEGER DEFAULT 0,
                daily_requests_limit   INTEGER NOT NULL,
                daily_tokens_used      INTEGER DEFAULT 0,
                daily_tokens_limit     INTEGER NOT NULL,
                last_reset_date        TEXT NOT NULL,
                is_active              INTEGER DEFAULT 1,
                priority_order         INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS prompt_traces (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT NOT NULL,
                provider       TEXT NOT NULL,
                model          TEXT NOT NULL,
                latency_ms     REAL NOT NULL,
                status         TEXT NOT NULL,
                prompt_snippet TEXT,
                output_snippet TEXT,
                input_tokens   INTEGER DEFAULT 0,
                output_tokens  INTEGER DEFAULT 0,
                error_message  TEXT
            );

            CREATE TABLE IF NOT EXISTS tone_profiles (
                slug                TEXT PRIMARY KEY,
                name                TEXT NOT NULL,
                description         TEXT NOT NULL,
                instructions        TEXT NOT NULL,
                example_output      TEXT,
                is_default          INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS plugins (
                name        TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                description TEXT NOT NULL,
                enabled     INTEGER DEFAULT 1,
                config_json TEXT DEFAULT '{}'
            );
            """
        )

        # Seed Default Tone Profiles
        tones = [
            (
                "casual",
                "Casual & Friendly",
                "Warm, relaxed, natural WhatsApp-style voice with light punctuation.",
                "Adopt a friendly, approachable, conversational tone. Keep it concise, natural, and helpful. Use simple phrasing suitable for WhatsApp or instant messaging. Do not use corporate jargon.",
                "Hey! Thanks so much for reaching out. Yes, we definitely have beginner classes on Mondays and Wednesdays. Would you like to come try one out?",
                0,
            ),
            (
                "professional",
                "Professional & Crisp",
                "Courteous, business-grade reply suitable for executive or formal email.",
                "Adopt a polite, crisp, and professional business tone. Acknowledge the inquiry promptly, provide clear next steps, and sign off respectfully.",
                "Dear client, thank you for contacting us. We have received your inquiry and would be glad to assist you. Our schedule has openings early next week—please let us know what time works best for you.",
                1,
            ),
            (
                "direct",
                "Direct & Concise",
                "Short, punchy 1-2 sentence response. Zero pleasantry fluff.",
                "Keep the reply extremely brief, clear, and direct. Max 2 sentences. Give the exact answer and a single direct question or call to action.",
                "Got your note! Yes, beginner slots are open Monday 6am and Wednesday 6pm. Which one suits you?",
                0,
            ),
            (
                "empathetic",
                "Warm & Empathetic",
                "Supportive, reassuring, and relationship-first tone for wellness or support.",
                "Be exceptionally welcoming, encouraging, and understanding. Acknowledge any hesitation or questions gently and invite them in with zero pressure.",
                "Hi there! Thank you so much for reaching out to us. Starting a new routine can feel daunting, but our community is super welcoming and beginner-friendly. We'd love to host you for a trial whenever you feel ready!",
                0,
            ),
            (
                "urgent_booking",
                "Conversion & Booking",
                "Action-oriented first reply to lock in a trial or schedule a call.",
                "Focus on immediate momentum and simple booking. Offer specific available times and ask for their preference to secure their reservation.",
                "Thanks for reaching out! We'd love to get you scheduled for a free trial class. We have Mon 6:00am, Wed 6:00pm, or Sat 8:00am open. Which slot can we reserve for you?",
                0,
            ),
        ]
        for slug, name, desc, inst, ex, is_def in tones:
            conn.execute(
                """
                INSERT OR IGNORE INTO tone_profiles (slug, name, description, instructions, example_output, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (slug, name, desc, inst, ex, is_def),
            )

        # Seed Quota Limits for Verified Free Providers (Reset daily)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        quotas = [
            ("ollama", "Local Ollama / llama.cpp", "llama3.2:3b / qwen2.5:3b", 1, 0, 999999, 0, 999999999, today_str, 1, 1),
            ("groq", "Groq Free Tier", "llama-3.3-70b-versatile", 0, 0, 14400, 0, 1000000, today_str, 1, 2),
            ("gemini", "Google Gemini Free Tier", "gemini-2.5-flash", 0, 0, 1500, 0, 1000000, today_str, 1, 3),
            ("openrouter", "OpenRouter Free Models", "meta-llama/llama-3.2-3b-instruct:free", 0, 0, 500, 0, 500000, today_str, 1, 4),
            ("offline_template", "Deterministic Offline Engine", "rules-engine-v1", 1, 0, 999999, 0, 999999999, today_str, 1, 5),
        ]
        for p, d, m, is_loc, u_req, l_req, u_tok, l_tok, r_date, is_act, prio in quotas:
            conn.execute(
                """
                INSERT OR IGNORE INTO quotas 
                (provider, display_name, model, is_local, daily_requests_used, daily_requests_limit, daily_tokens_used, daily_tokens_limit, last_reset_date, is_active, priority_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (p, d, m, is_loc, u_req, l_req, u_tok, l_tok, r_date, is_act, prio),
            )

        # Seed Settings
        default_settings = [
            ("local_only_mode", "false"),
            ("max_output_tokens", "256"),
            ("groq_api_key", ""),
            ("gemini_api_key", ""),
            ("openrouter_api_key", ""),
            ("ollama_base_url", "http://localhost:11434/v1"),
            ("default_tone", "casual"),
            ("user_name", "Daylon Naidoo"),
            ("business_name", "BCComputers / Local Studio"),
            ("hotkey", "Ctrl+Shift+R"),
        ]
        for k, v in default_settings:
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

        # Seed Plugins
        default_plugins = [
            ("clipboard", "Universal Clipboard Hook", "Listens for text copied to OS clipboard and offers instant reply draft.", 1),
            ("whatsapp", "WhatsApp Web Companion", "Formats instant conversational replies sized for WhatsApp web chats.", 1),
            ("email", "Desktop Email Formatter", "Formats crisp email drafts with greeting, bulleted body, and sign-off.", 1),
            ("telegram", "Telegram Bot Automator", "Official automated customer support bot with instant LLM responses.", 1),
        ]
        for p_name, p_title, p_desc, p_en in default_plugins:
            conn.execute(
                "INSERT OR IGNORE INTO plugins (name, title, description, enabled) VALUES (?, ?, ?, ?)",
                (p_name, p_title, p_desc, p_en),
            )


# ── Database Operations ───────────────────────────────────────────────────────

def log_reply_history(
    source_channel: str,
    original_text: str,
    reply_text: str,
    tone: str,
    provider_used: str,
    model_used: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Log an event in reply history."""
    now_iso = datetime.now(timezone.utc).isoformat()
    managed = conn is None
    c = conn or get_connection()
    try:
        cur = c.execute(
            """
            INSERT INTO history 
            (source_channel, original_text, reply_text, tone, provider_used, model_used, latency_ms, input_tokens, output_tokens, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (source_channel, original_text, reply_text, tone, provider_used, model_used, latency_ms, input_tokens, output_tokens, now_iso),
        )
        if managed:
            c.commit()
        return cur.lastrowid
    finally:
        if managed:
            c.close()


def get_recent_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent history items."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def mark_history_action(history_id: int, action: str) -> None:
    """Update approval or copy status on history record."""
    col = "approved" if action == "approve" else "copied"
    with get_connection() as conn:
        conn.execute(f"UPDATE history SET {col} = 1 WHERE id = ?", (history_id,))
        conn.commit()


def log_prompt_trace(
    provider: str,
    model: str,
    latency_ms: float,
    status: str,
    prompt_snippet: str,
    output_snippet: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error_message: Optional[str] = None,
) -> None:
    """Log fine-grained model execution trace."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prompt_traces 
            (timestamp, provider, model, latency_ms, status, prompt_snippet, output_snippet, input_tokens, output_tokens, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now_iso, provider, model, latency_ms, status, prompt_snippet[:300], output_snippet[:300], input_tokens, output_tokens, error_message),
        )
        conn.commit()


def get_recent_traces(limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch recent execution traces for /dev dashboard."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM prompt_traces ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_quotas() -> List[Dict[str, Any]]:
    """Retrieve all quota statuses."""
    _check_and_reset_daily_quotas()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM quotas ORDER BY priority_order ASC").fetchall()
        return [dict(r) for r in rows]


def update_quota_consumption(provider: str, req_count: int, token_count: int) -> None:
    """Increment consumed quota for a provider."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE quotas 
            SET daily_requests_used = daily_requests_used + ?,
                daily_tokens_used = daily_tokens_used + ?
            WHERE provider = ?
            """,
            (req_count, token_count, provider),
        )
        conn.commit()


def _check_and_reset_daily_quotas() -> None:
    """Reset daily counters if date has rolled over."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE quotas 
            SET daily_requests_used = 0,
                daily_tokens_used = 0,
                last_reset_date = ?
            WHERE last_reset_date != ?
            """,
            (today_str, today_str),
        )
        conn.commit()


def get_tone_profiles() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tone_profiles ORDER BY is_default DESC, name ASC").fetchall()
        return [dict(r) for r in rows]


def get_tone_profile(slug: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tone_profiles WHERE slug = ?", (slug,)).fetchone()
        return dict(row) if row else None


def get_all_settings() -> Dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        settings = {r["key"]: r["value"] for r in rows}
    
    # Fallback to environment variables or .env file if available
    env_keys = {
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "groq_api_key": "GROQ_API_KEY",
        "gemini_api_key": "GEMINI_API_KEY",
        "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    }
    for setting_k, env_k in env_keys.items():
        if not settings.get(setting_k):
            val = os.getenv(env_k, "").strip()
            if val:
                settings[setting_k] = val

    # Read from .env if still missing
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    for setting_k, env_k in env_keys.items():
                        if k == env_k and v and not settings.get(setting_k):
                            settings[setting_k] = v
        except Exception:
            pass

    return settings


def update_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()


def get_plugins() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM plugins").fetchall()
        return [dict(r) for r in rows]


def toggle_plugin(name: str, enabled: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE plugins SET enabled = ? WHERE name = ?", (1 if enabled else 0, name))
        conn.commit()
