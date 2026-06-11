"""Registry service tests — Phase 1."""
import pytest

TIMESHEET_MANIFEST = {
    "manifest": "0.1",
    "capability": {
        "id": "acme.timesheet", "name": "Timesheet Management",
        "description": "Submit and approve timesheets", "owner": "payroll-team",
        "lifecycle": "ga", "version": "1.0.0",
    },
    "runtime": {"base_url": "http://localhost:8101", "health_url": "/healthz", "fulfillment_modes": ["direct"]},
    "auth": {"idp": "keycloak", "audience": "timesheet-service", "scopes": ["timesheet.read", "timesheet.approve"]},
    "entities": [{"type": "Timesheet", "owns": True}],
    "intents": [{"id": "approve_timesheet", "description": "Approve a timesheet", "utterances": ["approve timesheet for {employee}"]}],
    "actions": [{
        "id": "approve_timesheet_action", "risk": "consequential",
        "confirmation": {"template": "Approve timesheet for {{employee.full_name}}", "show_fields": ["employee.full_name"], "requires": ["explicit_tap"], "voice_blocked": True},
    }],
}

DIRECTORY_MANIFEST = {
    "manifest": "0.1",
    "capability": {
        "id": "acme.directory", "name": "People Directory",
        "description": "Employee directory", "owner": "hr-team",
        "lifecycle": "ga", "version": "1.0.0",
    },
    "runtime": {"base_url": "http://localhost:8102", "health_url": "/healthz", "fulfillment_modes": ["direct"]},
    "auth": {"idp": "keycloak", "audience": "directory-service", "scopes": ["directory.read"]},
    "entities": [{"type": "Employee", "owns": True}, {"type": "Team", "owns": True}],
    "intents": [{"id": "find_employee", "description": "Find an employee", "utterances": ["find {employee}"]}],
    "actions": [{"id": "get_employee", "risk": "read"}],
}


async def test_healthz(client):
    """Every service has /healthz before anything else."""
    r = await client.get("/healthz")
    assert r.status_code == 200


async def test_register_capability(client):
    """POST /capabilities registers a valid manifest."""
    r = await client.post("/capabilities", json={"manifest": TIMESHEET_MANIFEST})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "acme.timesheet"
    assert data["lifecycle"] == "ga"


async def test_get_capability(client):
    """GET /capabilities/{id} returns the registered manifest."""
    await client.post("/capabilities", json={"manifest": TIMESHEET_MANIFEST})
    r = await client.get("/capabilities/acme.timesheet")
    assert r.status_code == 200
    assert r.json()["id"] == "acme.timesheet"


async def test_list_capabilities(client):
    """GET /capabilities lists all registered capabilities."""
    await client.post("/capabilities", json={"manifest": TIMESHEET_MANIFEST})
    await client.post("/capabilities", json={"manifest": DIRECTORY_MANIFEST})
    r = await client.get("/capabilities")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    ids = {c["id"] for c in data["capabilities"]}
    assert "acme.timesheet" in ids
    assert "acme.directory" in ids


async def test_duplicate_entity_ownership_rejected(client):
    """Composition check: two capabilities cannot own the same entity type."""
    await client.post("/capabilities", json={"manifest": TIMESHEET_MANIFEST})
    # Try to register another capability claiming Timesheet
    duplicate = {**TIMESHEET_MANIFEST}
    duplicate = dict(TIMESHEET_MANIFEST)
    duplicate["capability"] = {**TIMESHEET_MANIFEST["capability"], "id": "acme.other"}
    r = await client.post("/capabilities", json={"manifest": duplicate})
    assert r.status_code == 409


async def test_unknown_capability_404(client):
    """GET /capabilities/{id} returns 404 for unknown capability."""
    r = await client.get("/capabilities/acme.nonexistent")
    assert r.status_code == 404


async def test_bad_lifecycle_rejected(client):
    """Registry validates lifecycle enum."""
    bad = dict(TIMESHEET_MANIFEST)
    bad["capability"] = {**TIMESHEET_MANIFEST["capability"], "lifecycle": "production"}
    r = await client.post("/capabilities", json={"manifest": bad})
    assert r.status_code == 422


async def test_upsert_updates_existing(client):
    """Publishing same capability ID again updates it (upsert)."""
    await client.post("/capabilities", json={"manifest": TIMESHEET_MANIFEST})
    updated = dict(TIMESHEET_MANIFEST)
    updated["capability"] = {**TIMESHEET_MANIFEST["capability"], "version": "2.0.0"}
    r = await client.post("/capabilities", json={"manifest": updated})
    assert r.status_code == 200
    r2 = await client.get("/capabilities/acme.timesheet")
    assert r2.json()["version"] == "2.0.0"
