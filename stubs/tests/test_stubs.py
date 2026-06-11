"""Cross-stub integration tests — Phase 0 gate."""
import os
import pytest
import yaml
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


# ── Health checks ──────────────────────────────────────────────────────────

async def test_timesheet_healthz(ts_client):
    """Phase 0: all stubs healthy."""
    r = await ts_client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_people_healthz(pd_client):
    """Phase 0: all stubs healthy."""
    r = await pd_client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_permissions_healthz(perm_client):
    """Phase 0: all stubs healthy."""
    r = await perm_client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── OpenAPI validity ────────────────────────────────────────────────────────

async def test_timesheet_openapi_valid(ts_client):
    """All stubs expose valid OpenAPI docs."""
    r = await ts_client.get("/openapi.json")
    assert r.status_code == 200
    doc = r.json()
    assert "openapi" in doc
    assert "paths" in doc


async def test_people_openapi_valid(pd_client):
    """All stubs expose valid OpenAPI docs."""
    r = await pd_client.get("/openapi.json")
    assert r.status_code == 200
    doc = r.json()
    assert "openapi" in doc


async def test_permissions_openapi_valid(perm_client):
    """All stubs expose valid OpenAPI docs."""
    r = await perm_client.get("/openapi.json")
    assert r.status_code == 200
    doc = r.json()
    assert "openapi" in doc


# ── Capability YAML validation ──────────────────────────────────────────────

def load_yaml(stub_dir, filename="capability.yaml"):
    path = os.path.join(ROOT, "stubs", stub_dir, filename)
    with open(path) as f:
        return yaml.safe_load(f)


def test_timesheet_capability_yaml_structure():
    """Phase 0: xp validate passes on timesheet manifest."""
    manifest = load_yaml("timesheet")
    assert manifest["manifest"] == "0.1"
    assert manifest["capability"]["id"] == "acme.timesheet"
    assert manifest["capability"]["lifecycle"] in ("draft", "beta", "ga", "deprecated")
    assert len(manifest["runtime"]["fulfillment_modes"]) >= 1
    assert len(manifest["auth"]["scopes"]) >= 1


def test_people_capability_yaml_structure():
    """Phase 0: xp validate passes on people-data manifest."""
    manifest = load_yaml("people-data")
    assert manifest["manifest"] == "0.1"
    assert manifest["capability"]["id"] == "acme.directory"
    assert manifest["capability"]["lifecycle"] in ("draft", "beta", "ga", "deprecated")


def test_permissions_capability_yaml_structure():
    """Phase 0: xp validate passes on permissions manifest."""
    manifest = load_yaml("permissions")
    assert manifest["manifest"] == "0.1"
    assert manifest["capability"]["id"] == "acme.permissions"


# ── Consequential actions must have confirmation blocks ─────────────────────

def test_timesheet_consequential_has_confirmation():
    """INV-5: consequential actions must declare confirmation blocks."""
    manifest = load_yaml("timesheet")
    for action in manifest.get("actions", []):
        if action["risk"] == "consequential":
            assert "confirmation" in action, f"Action {action['id']} missing confirmation"
            assert "template" in action["confirmation"]
            assert action["confirmation"].get("voice_blocked") is True


# ── No duplicate entity ownership ──────────────────────────────────────────

def test_no_duplicate_entity_ownership_across_stubs():
    """Registry composition check: no two capabilities own the same entity type."""
    owned: dict[str, str] = {}
    for stub_dir in ("timesheet", "people-data", "permissions"):
        manifest = load_yaml(stub_dir)
        cap_id = manifest["capability"]["id"]
        for entity in manifest.get("entities", []):
            if entity.get("owns"):
                etype = entity["type"]
                assert etype not in owned, (
                    f"Entity type {etype!r} claimed by both {owned[etype]} and {cap_id}"
                )
                owned[etype] = cap_id


# ── Cross-stub data consistency ─────────────────────────────────────────────

async def test_timesheet_employee_resolves_in_directory(ts_client, pd_client):
    """INV-3: entity spine — timesheet employee IDs resolve in directory."""
    r = await ts_client.get("/timesheets/TS-001")
    ts_data = r.json()
    employee_id = ts_data["timesheet"]["employee_id"]

    r = await pd_client.get(f"/employees/{employee_id}")
    assert r.status_code == 200
    assert r.json()["employee_id"] == employee_id


async def test_manager_permission_for_timesheet_approval(perm_client):
    """P4: trust check — manager can approve timesheets."""
    r = await perm_client.post("/permissions/check", json={
        "user_id": "E-10004",
        "action": "timesheet.approve",
        "resource_type": "Timesheet",
    })
    assert r.status_code == 200
    assert r.json()["allowed"] is True


async def test_engineer_blocked_from_timesheet_approval(perm_client):
    """P4: trust check — engineers cannot approve timesheets."""
    r = await perm_client.post("/permissions/check", json={
        "user_id": "E-10001",
        "action": "timesheet.approve",
        "resource_type": "Timesheet",
    })
    assert r.status_code == 200
    assert r.json()["allowed"] is False


async def test_idempotency_key_accepted_on_submit(ts_client):
    """Stubs support Idempotency-Key header on write operations."""
    r = await ts_client.post(
        "/timesheets/TS-002/submit",
        json={"submitted_by": "bob@acme.com"},
        headers={"Idempotency-Key": "idem-key-001"},
    )
    assert r.status_code == 200
    assert r.json()["idempotency_key"] == "idem-key-001"
