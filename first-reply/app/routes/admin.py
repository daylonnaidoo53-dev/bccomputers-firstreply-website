"""
app/routes/admin.py — Admin inspection and reporting endpoints.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response

import config
import database as db

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_admin_auth(x_admin_token: str | None) -> None:
    expected = config.cfg.admin_token
    if not x_admin_token or not expected or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/leads")
async def get_leads(x_admin_token: str | None = Header(default=None)) -> list[dict[str, Any]]:
    """Return all leads as JSON, newest first."""
    _check_admin_auth(x_admin_token)
    return db.all_leads()


@router.get("/leads.csv")
async def get_leads_csv(x_admin_token: str | None = Header(default=None)) -> Response:
    """Download leads log as CSV."""
    _check_admin_auth(x_admin_token)
    content = db.leads_as_csv()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
