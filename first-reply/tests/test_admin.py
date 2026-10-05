"""
tests/test_admin.py — Admin route authentication and reporting.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations


def test_leads_requires_token(client):
    # Without header -> 401
    resp = client.get("/admin/leads")
    assert resp.status_code == 401

    # With invalid header -> 401
    resp_invalid = client.get("/admin/leads", headers={"X-Admin-Token": "bad-token"})
    assert resp_invalid.status_code == 401

    # With valid header -> 200
    resp_valid = client.get("/admin/leads", headers={"X-Admin-Token": "test-admin-token"})
    assert resp_valid.status_code == 200
    assert isinstance(resp_valid.json(), list)


def test_csv_requires_token(client):
    resp = client.get("/admin/leads.csv")
    assert resp.status_code == 401


def test_csv_downloads(client):
    resp = client.get(
        "/admin/leads.csv",
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=leads.csv" in resp.headers.get("content-disposition", "")
