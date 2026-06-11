"""Router tests — Phase 1. P6: compiled paths are the performance contract."""
import pytest


async def test_healthz(client):
    """Every service has /healthz."""
    r = await client.get("/healthz")
    assert r.status_code == 200


async def test_exact_utterance_routes(client):
    """Known utterance routes to correct capability and intent."""
    r = await client.post("/route", json={"utterance": "submit my timesheet"})
    assert r.status_code == 200
    data = r.json()
    assert data["routed"] is True
    assert data["result"]["capability_id"] == "acme.timesheet"
    assert data["result"]["intent_id"] == "submit_timesheet"


async def test_hot_path_on_second_call(client):
    """P6: second identical call uses compiled hot path — model not invoked."""
    utterance = "approve timesheet for alice"
    await client.post("/route", json={"utterance": utterance})
    r2 = await client.post("/route", json={"utterance": utterance})
    assert r2.status_code == 200
    data = r2.json()
    assert data["routed"] is True
    assert data["result"]["compiled"] is True


async def test_unknown_utterance_needs_clarification(client):
    """Unrecognized utterance returns clarification needed, not a guess (INV-3)."""
    r = await client.post("/route", json={"utterance": "xyzzy foobar baz quux norf"})
    assert r.status_code == 200
    data = r.json()
    assert data["routed"] is False
    assert data["clarification"]["needs_clarification"] is True


async def test_case_insensitive_routing(client):
    """Router is case-insensitive."""
    r = await client.post("/route", json={"utterance": "SUBMIT MY TIMESHEET"})
    assert r.status_code == 200
    data = r.json()
    assert data["routed"] is True
    assert data["result"]["capability_id"] == "acme.timesheet"


async def test_partial_utterance_routes(client):
    """Utterance with slot filled routes to correct intent."""
    r = await client.post("/route", json={"utterance": "approve timesheet for bob"})
    assert r.status_code == 200
    data = r.json()
    assert data["routed"] is True
    assert data["result"]["intent_id"] == "approve_timesheet"


async def test_directory_intent_routes(client):
    """Directory capability intent routes correctly."""
    r = await client.post("/route", json={"utterance": "find alice"})
    assert r.status_code == 200
    data = r.json()
    assert data["routed"] is True
    assert data["result"]["capability_id"] == "acme.directory"
