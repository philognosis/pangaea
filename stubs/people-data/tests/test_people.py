import pytest


async def test_healthz(client):
    """Northstar: every service has /healthz before anything else."""
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_list_employees(client):
    """Directory returns all seeded employees."""
    r = await client.get("/employees")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert len(data["employees"]) == 4


async def test_get_employee(client):
    """INV-3: entity spine resolves canonical Employee by ID."""
    r = await client.get("/employees/E-10001")
    assert r.status_code == 200
    emp = r.json()
    assert emp["employee_id"] == "E-10001"
    assert emp["full_name"] == "Alice Smith"


async def test_search_employees(client):
    """Entity resolution search endpoint returns matching employees."""
    r = await client.get("/employees/search?q=alice")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["employees"][0]["employee_id"] == "E-10001"


async def test_get_nonexistent_employee(client):
    """404 on unknown employee — no silent guessing (INV-3)."""
    r = await client.get("/employees/E-99999")
    assert r.status_code == 404


async def test_filter_by_team(client):
    """Team filter works on employee listing."""
    r = await client.get("/employees?team_id=T-001")
    assert r.status_code == 200
    data = r.json()
    assert all(e["team_id"] == "T-001" for e in data["employees"])
