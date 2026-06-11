from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from datetime import datetime, timezone
from timesheet_models import (
    Timesheet, TimesheetStatus, Employee,
    SubmitRequest, ApproveRequest,
)

app = FastAPI(title="Timesheet Stub", version="1.0.0")

EMPLOYEES: dict[str, Employee] = {
    "E-10001": Employee(employee_id="E-10001", full_name="Alice Smith", email="alice@acme.com", team="Engineering"),
    "E-10002": Employee(employee_id="E-10002", full_name="Bob Jones", email="bob@acme.com", team="Engineering"),
    "E-10003": Employee(employee_id="E-10003", full_name="Carol White", email="carol@acme.com", team="HR"),
}

_SEED_TIMESHEETS: dict[str, dict] = {
    "TS-001": dict(timesheet_id="TS-001", employee_id="E-10001", employee_name="Alice Smith",
                   period="2025-W24", total_hours=40.0, status=TimesheetStatus.SUBMITTED,
                   submitted_at="2025-06-10T09:00:00Z"),
    "TS-002": dict(timesheet_id="TS-002", employee_id="E-10002", employee_name="Bob Jones",
                   period="2025-W24", total_hours=38.5, status=TimesheetStatus.DRAFT),
}

TIMESHEETS: dict[str, Timesheet] = {k: Timesheet(**v) for k, v in _SEED_TIMESHEETS.items()}
_approved_calls: list[dict] = []


def reset():
    global TIMESHEETS, _approved_calls
    TIMESHEETS = {k: Timesheet(**v) for k, v in _SEED_TIMESHEETS.items()}
    _approved_calls.clear()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "timesheet-stub"}


@app.get("/openapi.json", include_in_schema=False)
def openapi():
    return app.openapi()


@app.get("/timesheets")
def list_timesheets(status: Optional[str] = None):
    ts = list(TIMESHEETS.values())
    if status:
        ts = [t for t in ts if t.status.value == status]
    return {"timesheets": [t.model_dump() for t in ts]}


@app.get("/timesheets/search")
def search_timesheets(q: str = ""):
    results = [t for t in TIMESHEETS.values() if q.lower() in t.employee_name.lower()]
    return {"results": [t.model_dump() for t in results]}


@app.get("/timesheets/{timesheet_id}")
def get_timesheet(timesheet_id: str):
    ts = TIMESHEETS.get(timesheet_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    employee = EMPLOYEES.get(ts.employee_id)
    return {"timesheet": ts.model_dump(), "employee": employee.model_dump() if employee else None}


@app.post("/timesheets/{timesheet_id}/submit")
def submit_timesheet(
    timesheet_id: str,
    req: SubmitRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    ts = TIMESHEETS.get(timesheet_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    if ts.status not in (TimesheetStatus.DRAFT, TimesheetStatus.REJECTED):
        raise HTTPException(status_code=409, detail="Timesheet already submitted")
    ts.status = TimesheetStatus.SUBMITTED
    ts.submitted_at = datetime.now(timezone.utc).isoformat()
    return {"timesheet_id": timesheet_id, "status": ts.status, "idempotency_key": idempotency_key}


@app.post("/timesheets/{timesheet_id}/approve")
def approve_timesheet(
    timesheet_id: str,
    req: ApproveRequest,
    authorization: Optional[str] = Header(None),
):
    ts = TIMESHEETS.get(timesheet_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    if ts.status != TimesheetStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="Timesheet not in submitted state")
    ts.status = TimesheetStatus.APPROVED
    ts.approved_at = datetime.now(timezone.utc).isoformat()
    ts.approved_by = req.approved_by
    _approved_calls.append({
        "timesheet_id": timesheet_id,
        "token": authorization,
        "approved_by": req.approved_by,
    })
    return {"timesheet_id": timesheet_id, "status": ts.status, "approved_by": req.approved_by}


@app.get("/internal/approved_calls")
def get_approved_calls():
    return {"calls": _approved_calls}
