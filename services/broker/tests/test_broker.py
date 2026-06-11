"""Token broker tests — Phase 1. INV-1 security invariants."""
import pytest
from broker.exchange import decode_token


async def test_healthz(client):
    """Every service has /healthz."""
    r = await client.get("/healthz")
    assert r.status_code == 200


async def test_valid_token_exchange(client):
    """Valid exchange returns a scoped OBO token."""
    r = await client.post("/token/exchange", json={
        "user_token": "Bearer alice-token",
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.approve"],
        "ttl_seconds": 300,
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["scopes"] == ["timesheet.approve"]
    assert data["capability_id"] == "acme.timesheet"
    assert data["expires_in"] == 300


async def test_over_scoped_request_rejected(client):
    """INV-1: broker cannot mint token for scopes not in manifest."""
    r = await client.post("/token/exchange", json={
        "user_token": "Bearer alice-token",
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.admin"],  # not in manifest
        "ttl_seconds": 300,
    })
    assert r.status_code == 403
    assert "not in manifest" in r.json()["detail"]


async def test_ttl_exceeds_limit_rejected(client):
    """INV-1: no token stored longer than 600s."""
    r = await client.post("/token/exchange", json={
        "user_token": "Bearer alice-token",
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.approve"],
        "ttl_seconds": 601,
    })
    assert r.status_code == 403
    assert "600" in r.json()["detail"]


async def test_unknown_capability_rejected(client):
    """Broker rejects exchange for unregistered capability."""
    r = await client.post("/token/exchange", json={
        "user_token": "Bearer alice-token",
        "capability_id": "acme.nonexistent",
        "required_scopes": ["some.scope"],
        "ttl_seconds": 300,
    })
    assert r.status_code == 404


async def test_token_contains_correct_scopes(client):
    """Minted token payload contains exactly the requested scopes."""
    r = await client.post("/token/exchange", json={
        "user_token": "Bearer manager-token",
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.approve"],
        "ttl_seconds": 300,
    })
    assert r.status_code == 200
    token = r.json()["access_token"]
    payload = decode_token(token)
    assert payload["scopes"] == ["timesheet.approve"]
    assert payload["aud"] == "acme.timesheet"


async def test_invalid_bearer_token_rejected(client):
    """Broker rejects requests without a Bearer token."""
    r = await client.post("/token/exchange", json={
        "user_token": "not-a-bearer-token",
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.approve"],
        "ttl_seconds": 300,
    })
    assert r.status_code == 401
