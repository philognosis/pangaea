import pytest


async def test_healthz(client):
    """Northstar: every service has /healthz before anything else."""
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_manager_can_approve_timesheet(client):
    """P4 trust chain: manager role permits timesheet.approve action."""
    r = await client.post("/permissions/check", json={
        "user_id": "E-10004",
        "action": "timesheet.approve",
        "resource_type": "Timesheet",
    })
    assert r.status_code == 200
    assert r.json()["allowed"] is True


async def test_engineer_cannot_approve_timesheet(client):
    """P4 trust chain: engineer role denies timesheet.approve action."""
    r = await client.post("/permissions/check", json={
        "user_id": "E-10001",
        "action": "timesheet.approve",
        "resource_type": "Timesheet",
    })
    assert r.status_code == 200
    assert r.json()["allowed"] is False


async def test_get_user_permissions(client):
    """User permissions profile returns roles and capabilities."""
    r = await client.get("/permissions/user/E-10004")
    assert r.status_code == 200
    data = r.json()
    assert "manager" in data["roles"]
    assert "timesheet.approve" in data["capabilities"]


async def test_unknown_user_404(client):
    """Unknown user returns 404 — no silent guessing (INV-3)."""
    r = await client.get("/permissions/user/E-99999")
    assert r.status_code == 404
