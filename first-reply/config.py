"""
config.py — Loads config.yaml and .env into a typed Config object.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent
_ENV_PATH = _ROOT / ".env"
load_dotenv(_ENV_PATH)


@dataclass
class Config:
    # --- Business facts (from config.yaml) ---
    business_name: str
    city: str
    offer_name: str
    trial_slots: list[str]
    owner_whatsapp: str
    owner_email: str
    booking_link: str
    llm_polish: bool
    sla_seconds: int

    # --- Secrets and environment settings (from .env) ---
    admin_token: str = field(
        default_factory=lambda: os.environ.get("ADMIN_TOKEN", "dev-admin-token")
    )
    whatsapp_verify_token: str = field(
        default_factory=lambda: os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    )
    whatsapp_app_secret: str = field(
        default_factory=lambda: os.environ.get("WHATSAPP_APP_SECRET", "")
    )
    whatsapp_access_token: str = field(
        default_factory=lambda: os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
    )
    whatsapp_phone_number_id: str = field(
        default_factory=lambda: os.environ.get(
            "WHATSAPP_PHONE_NUMBER_ID", os.environ.get("WHATSAPP_PHONE_ID", "")
        )
    )

    smtp_host: str = field(default_factory=lambda: os.environ.get("SMTP_HOST", ""))
    smtp_port: int = field(
        default_factory=lambda: int(os.environ.get("SMTP_PORT", "587"))
    )
    smtp_user: str = field(default_factory=lambda: os.environ.get("SMTP_USER", ""))
    smtp_password: str = field(
        default_factory=lambda: os.environ.get("SMTP_PASSWORD", "")
    )
    smtp_use_tls: bool = field(
        default_factory=lambda: os.environ.get("SMTP_USE_TLS", "true").lower()
        in {"true", "1", "yes"}
    )
    from_email: str = field(
        default_factory=lambda: os.environ.get(
            "FROM_EMAIL", os.environ.get("SMTP_FROM", "")
        )
    )

    openai_api_key: str = field(
        default_factory=lambda: os.environ.get(
            "OPENAI_API_KEY", os.environ.get("LLM_API_KEY", "")
        )
    )
    openai_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "OPENAI_BASE_URL",
            os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        )
    )
    openai_model: str = field(
        default_factory=lambda: os.environ.get(
            "OPENAI_MODEL", os.environ.get("LLM_MODEL", "gpt-4o-mini")
        )
    )
    db_path: str = field(default_factory=lambda: os.environ.get("DB_PATH", ""))


def load_config(yaml_path: Optional[Path] = None) -> Config:
    """Load configuration from config.yaml and environment."""
    if yaml_path is None:
        yaml_path = _ROOT / "config.yaml"

    with open(yaml_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return Config(
        business_name=raw.get("business_name", ""),
        city=raw.get("city", ""),
        offer_name=raw.get("offer_name", ""),
        trial_slots=raw.get("trial_slots", []),
        owner_whatsapp=raw.get("owner_whatsapp", ""),
        owner_email=raw.get("owner_email", ""),
        booking_link=raw.get("booking_link", "") or "",
        llm_polish=raw.get("llm_polish", False),
        sla_seconds=int(raw.get("sla_seconds", 120)),
    )


cfg: Config = load_config()
