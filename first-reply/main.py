"""
main.py — FastAPI application entry point with lifespan management.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

# Ensure project root is available for imports
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI

import database
from app.routes.admin import router as admin_router
from app.routes.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan managing database startup."""
    database.init_db()
    yield


app = FastAPI(
    title="First Reply Service — Fitness Fuzion",
    description="Automated first-reply service. Author: Daylon Naido · BCComputers",
    lifespan=lifespan,
)

app.include_router(webhooks_router)
app.include_router(admin_router)
