"""Provenance ledger tests — Phase 1. INV-5: receipt before dispatch."""
import pytest
import hashlib
from gateway.ledger import Ledger, _compute_chain_hash


@pytest.fixture
def ledger():
    l = Ledger()
    yield l
    l.reset()


def test_write_single_receipt(ledger):
    """Ledger accepts the first receipt with genesis prev_hash."""
    r = ledger.write_receipt(
        intent_text="Approve timesheet TS-001",
        capability_id="acme.timesheet",
        entity_json={"employee": "Alice Smith"},
        action_id="approve_timesheet_action",
        user_sub="manager@acme.com",
        card_hash="abc123",
        idempotency_key="idem-001",
    )
    assert r["id"] is not None
    assert r["prev_hash"] == Ledger.GENESIS_HASH
    assert r["chain_hash"] is not None


def test_chain_links_correctly(ledger):
    """Each receipt's chain_hash depends on the previous receipt's chain_hash."""
    r1 = ledger.write_receipt(
        intent_text="Action 1", capability_id="acme.timesheet",
        entity_json={}, action_id="action1", user_sub="user1",
        card_hash="hash1", idempotency_key="idem-001",
    )
    r2 = ledger.write_receipt(
        intent_text="Action 2", capability_id="acme.timesheet",
        entity_json={}, action_id="action2", user_sub="user2",
        card_hash="hash2", idempotency_key="idem-002",
    )
    assert r2["prev_hash"] == r1["chain_hash"]


def test_verify_chain_valid(ledger):
    """Unmodified chain verifies as valid and intact."""
    r1 = ledger.write_receipt(
        intent_text="Approve TS-001", capability_id="acme.timesheet",
        entity_json={}, action_id="approve_timesheet_action", user_sub="manager@acme.com",
        card_hash="abc123", idempotency_key="idem-001",
    )
    r2 = ledger.write_receipt(
        intent_text="Approve TS-002", capability_id="acme.timesheet",
        entity_json={}, action_id="approve_timesheet_action", user_sub="manager@acme.com",
        card_hash="def456", idempotency_key="idem-002",
    )
    result = ledger.verify_chain(r2["id"])
    assert result["valid"] is True
    assert result["chain_intact"] is True


def test_tampered_receipt_detected(ledger):
    """Chain integrity check detects tampered records."""
    r1 = ledger.write_receipt(
        intent_text="Approve TS-001", capability_id="acme.timesheet",
        entity_json={}, action_id="approve_timesheet_action", user_sub="manager@acme.com",
        card_hash="abc123", idempotency_key="idem-001",
    )
    # Tamper with the receipt
    ledger._receipts[0].card_hash = "tampered_hash"
    result = ledger.verify_chain(r1["id"])
    assert result["valid"] is False
    assert result["chain_intact"] is False


def test_idempotency_key_prevents_duplicate(ledger):
    """Duplicate idempotency_key raises 409 — prevents double-commit."""
    from fastapi import HTTPException
    ledger.write_receipt(
        intent_text="Action 1", capability_id="acme.timesheet",
        entity_json={}, action_id="action1", user_sub="user1",
        card_hash="hash1", idempotency_key="idem-unique",
    )
    with pytest.raises(HTTPException) as exc_info:
        ledger.write_receipt(
            intent_text="Action 1 again", capability_id="acme.timesheet",
            entity_json={}, action_id="action1", user_sub="user1",
            card_hash="hash1", idempotency_key="idem-unique",
        )
    assert exc_info.value.status_code == 409


def test_receipt_not_found_raises(ledger):
    """verify_chain raises 404 for unknown receipt_id."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        ledger.verify_chain("nonexistent-id")
    assert exc_info.value.status_code == 404
