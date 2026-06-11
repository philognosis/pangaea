from fastapi import FastAPI, HTTPException
import httpx
from gateway.models import PushEvent, ApproveRequest
from gateway.ledger import Ledger
from gateway.push import build_confirmation_card

app = FastAPI(title="Pangaea Gateway", version="0.1.0")
ledger = Ledger()

_push_events: list[dict] = []
_timesheet_client: httpx.AsyncClient | None = None
_broker_client: httpx.AsyncClient | None = None

TIMESHEET_BASE = "http://localhost:8101"
BROKER_BASE = "http://localhost:8200"


def configure(
    timesheet_client: httpx.AsyncClient | None = None,
    broker_client: httpx.AsyncClient | None = None,
):
    global _timesheet_client, _broker_client
    if timesheet_client is not None:
        _timesheet_client = timesheet_client
    if broker_client is not None:
        _broker_client = broker_client


def reset():
    global _push_events, _timesheet_client, _broker_client
    _push_events = []
    _timesheet_client = None
    _broker_client = None
    ledger.reset()


def _ts_client() -> httpx.AsyncClient:
    if _timesheet_client:
        return _timesheet_client
    return httpx.AsyncClient(base_url=TIMESHEET_BASE)


def _bk_client() -> httpx.AsyncClient:
    if _broker_client:
        return _broker_client
    return httpx.AsyncClient(base_url=BROKER_BASE)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "gateway"}


@app.post("/internal/push_event")
async def inject_push_event(event: PushEvent):
    """Simulate a NATS push event arriving at the gateway."""
    tc = _ts_client()
    r = await tc.get(f"/timesheets/{event.timesheet_id}")
    if r.status_code != 200:
        raise HTTPException(502, f"Timesheet stub error: {r.status_code}")
    ts_data = r.json()
    employee_data = ts_data.get("employee") or {}

    card = build_confirmation_card(
        timesheet_data=ts_data.get("timesheet", ts_data),
        employee_data=employee_data,
        action_id="approve_timesheet_action",
        capability_id="acme.timesheet",
    )
    push_record = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "capability_id": event.capability_id,
        "timesheet_id": event.timesheet_id,
        "card": card,
    }
    _push_events.append(push_record)
    return {"ok": True, "card_hash": card["card_hash"], "component_id": card["component_id"]}


@app.get("/internal/push_events")
def get_push_events():
    return {"events": _push_events, "count": len(_push_events)}


@app.post("/actions/approve")
async def approve_timesheet(req: ApproveRequest):
    """
    Process approval: write receipt BEFORE dispatch (INV-5), mint OBO token, dispatch.
    """
    pending = next((e for e in _push_events if e["timesheet_id"] == req.timesheet_id), None)
    if not pending:
        raise HTTPException(404, f"No pending push event for timesheet {req.timesheet_id!r}")

    card = pending["card"]

    # INV-5: write receipt BEFORE dispatch
    receipt = ledger.write_receipt(
        intent_text=f"Approve timesheet {req.timesheet_id}",
        capability_id="acme.timesheet",
        entity_json=card["props"]["fields"],
        action_id="approve_timesheet_action",
        user_sub=req.user_sub,
        card_hash=card["card_hash"],
        idempotency_key=req.idempotency_key,
    )
    receipt_id = receipt["id"]
    receipt_time = receipt["committed_at"]

    # Mint OBO token — exactly timesheet.approve, no extras
    bc = _bk_client()
    token_r = await bc.post("/token/exchange", json={
        "user_token": req.user_token,
        "capability_id": "acme.timesheet",
        "required_scopes": ["timesheet.approve"],
        "ttl_seconds": 300,
    })
    if token_r.status_code != 200:
        raise HTTPException(502, f"Token exchange failed: {token_r.text}")
    token_data = token_r.json()

    # Dispatch to timesheet stub
    tc = _ts_client()
    approve_r = await tc.post(
        f"/timesheets/{req.timesheet_id}/approve",
        json={"approved_by": req.user_sub, "timesheet_id": req.timesheet_id},
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    if approve_r.status_code != 200:
        raise HTTPException(502, f"Timesheet approval failed: {approve_r.text}")

    return {
        "status": "approved",
        "receipt_id": receipt_id,
        "receipt_committed_at": receipt_time,
        "scopes": token_data["scopes"],
        "expires_in": token_data["expires_in"],
        "timesheet_status": approve_r.json().get("status"),
    }


@app.get("/receipts")
def get_receipts():
    return {"receipts": ledger.receipts}


@app.get("/receipts/{receipt_id}/verify")
def verify_receipt(receipt_id: str):
    return ledger.verify_chain(receipt_id)
