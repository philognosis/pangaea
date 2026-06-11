import pytest


async def test_healthz(client):
    """Northstar: every service has a /healthz endpoint before anything else."""
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_list_timesheets(client):
    """Stub returns seed data for timesheet listing."""
    r = await client.get("/timesheets")
    assert r.status_code == 200
    data = r.json()
    assert "timesheets" in data
    assert len(data["timesheets"]) == 2


async def test_get_timesheet_with_employee(client):
    """INV-7: entity spine resolution — timesheet returns resolved employee data."""
    r = await client.get("/timesheets/TS-001")
    assert r.status_code == 200
    data = r.json()
    assert data["timesheet"]["timesheet_id"] == "TS-001"
    assert data["employee"]["employee_id"] == "E-10001"
    assert data["employee"]["full_name"] == "Alice Smith"


async def test_get_nonexistent_timesheet(client):
    """404 on unknown timesheet."""
    r = await client.get("/timesheets/TS-999")
    assert r.status_code == 404


async def test_submit_draft_timesheet(client):
    """Reversible action: submit transitions draft to submitted."""
    r = await client.post("/timesheets/TS-002/submit", json={"submitted_by": "bob@acme.com"})
    assert r.status_code == 200
    assert r.json()["status"] == "submitted"


async def test_approve_submitted_timesheet(client):
    """Consequential action: approve transitions submitted to approved."""
    r = await client.post(
        "/timesheets/TS-001/approve",
        json={"approved_by": "manager@acme.com", "timesheet_id": "TS-001"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert r.json()["approved_by"] == "manager@acme.com"


async def test_filter_timesheets_by_status(client):
    """Query parameter filtering works on list endpoint."""
    r = await client.get("/timesheets?status=submitted")
    assert r.status_code == 200
    ts = r.json()["timesheets"]
    assert len(ts) >= 1
    assert all(t["status"] == "submitted" for t in ts)
