"""
tests/conftest.py — Test configuration and fixtures.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import os

# CRITICAL: Set environment variables BEFORE any application imports
os.environ["WHATSAPP_APP_SECRET"] = "test-secret"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test-verify"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["WHATSAPP_ACCESS_TOKEN"] = ""
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = ""
os.environ["SMTP_HOST"] = ""
os.environ["OPENAI_API_KEY"] = ""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

# Reload config with test environment variables
config.cfg = config.load_config()

import database
from main import app


@pytest.fixture(autouse=True, scope="session")
def _temp_db(tmp_path_factory):
    """Use an isolated SQLite database for tests."""
    tmp = tmp_path_factory.mktemp("db")
    db_file = tmp / "leads_test.db"
    database.init_db(db_file)
    yield


@pytest.fixture(scope="session")
def client():
    """Test client for FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_sends():
    """Mock external dispatch calls to prevent real network I/O."""
    with (
        patch("app.adapters.form.FormAdapter.send", new_callable=AsyncMock) as _form,
        patch("app.adapters.whatsapp.WhatsAppAdapter.send", new_callable=AsyncMock) as _wa,
        patch("app.handoff.notify_owner", new_callable=AsyncMock) as _notify,
        patch("app.handoff.forward_to_owner", new_callable=AsyncMock) as _fwd,
    ):
        yield {
            "form_send": _form,
            "wa_send": _wa,
            "notify_owner": _notify,
            "forward_to_owner": _fwd,
        }
