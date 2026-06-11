"""
Append-only hash-chained provenance ledger.
INV-5: write_receipt() must complete before any consequential dispatch.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException


class Receipt:
    def __init__(
        self,
        receipt_id: str,
        intent_text: str,
        capability_id: str,
        entity_json: dict,
        action_id: str,
        user_sub: str,
        card_hash: str,
        idempotency_key: str,
        prev_hash: str,
        chain_hash: str,
        committed_at: str,
    ):
        self.id = receipt_id
        self.intent_text = intent_text
        self.capability_id = capability_id
        self.entity_json = entity_json
        self.action_id = action_id
        self.user_sub = user_sub
        self.card_hash = card_hash
        self.idempotency_key = idempotency_key
        self.prev_hash = prev_hash
        self.chain_hash = chain_hash
        self.committed_at = committed_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "intent_text": self.intent_text,
            "capability_id": self.capability_id,
            "entity_json": self.entity_json,
            "action_id": self.action_id,
            "user_sub": self.user_sub,
            "card_hash": self.card_hash,
            "idempotency_key": self.idempotency_key,
            "prev_hash": self.prev_hash,
            "chain_hash": self.chain_hash,
            "committed_at": self.committed_at,
        }


def _compute_chain_hash(prev_hash: str, receipt_id: str, card_hash: str, action_id: str, user_sub: str) -> str:
    content = f"{prev_hash}|{receipt_id}|{card_hash}|{action_id}|{user_sub}"
    return hashlib.sha256(content.encode()).hexdigest()


class Ledger:
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self._receipts: list[Receipt] = []
        self._idempotency_keys: set[str] = set()

    def reset(self):
        self._receipts.clear()
        self._idempotency_keys.clear()

    @property
    def receipts(self) -> list[dict]:
        return [r.to_dict() for r in self._receipts]

    def write_receipt(
        self,
        intent_text: str,
        capability_id: str,
        entity_json: dict,
        action_id: str,
        user_sub: str,
        card_hash: str,
        idempotency_key: str,
    ) -> dict:
        """Write a receipt. INV-5: must be called BEFORE dispatch."""
        if idempotency_key in self._idempotency_keys:
            raise HTTPException(409, f"Duplicate idempotency_key: {idempotency_key!r}")

        prev_hash = self._receipts[-1].chain_hash if self._receipts else self.GENESIS_HASH
        receipt_id = str(uuid.uuid4())
        chain_hash = _compute_chain_hash(prev_hash, receipt_id, card_hash, action_id, user_sub)

        receipt = Receipt(
            receipt_id=receipt_id,
            intent_text=intent_text,
            capability_id=capability_id,
            entity_json=entity_json,
            action_id=action_id,
            user_sub=user_sub,
            card_hash=card_hash,
            idempotency_key=idempotency_key,
            prev_hash=prev_hash,
            chain_hash=chain_hash,
            committed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._receipts.append(receipt)
        self._idempotency_keys.add(idempotency_key)
        return receipt.to_dict()

    def verify_chain(self, receipt_id: str) -> dict:
        """Verify chain integrity up to and including the given receipt."""
        target = next((r for r in self._receipts if r.id == receipt_id), None)
        if not target:
            raise HTTPException(404, f"Receipt not found: {receipt_id!r}")

        prev_hash = self.GENESIS_HASH
        for r in self._receipts:
            expected = _compute_chain_hash(prev_hash, r.id, r.card_hash, r.action_id, r.user_sub)
            if expected != r.chain_hash:
                return {"valid": False, "chain_intact": False, "broken_at": r.id}
            prev_hash = r.chain_hash
            if r.id == receipt_id:
                break

        return {"valid": True, "chain_intact": True, "receipt_id": receipt_id}

    def get_receipt(self, receipt_id: str) -> dict:
        r = next((r for r in self._receipts if r.id == receipt_id), None)
        if not r:
            raise HTTPException(404, f"Receipt not found: {receipt_id!r}")
        return r.to_dict()
