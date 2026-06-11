"""Push event store and ConfirmationCard builder."""
import hashlib
import json
from typing import Any


def build_card_hash(fields: dict[str, Any]) -> str:
    """SHA256 of the sorted fields JSON — used to detect tampering (INV-4)."""
    serialized = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def build_confirmation_card(timesheet_data: dict, employee_data: dict, action_id: str, capability_id: str) -> dict:
    """
    INV-4: Build confirmation card from resolved entity data only.
    The model provides zero input to this function.
    """
    ts = timesheet_data.get("timesheet", timesheet_data)
    emp = employee_data or {}

    fields = {
        "employee.full_name": emp.get("full_name", ""),
        "employee.employee_id": emp.get("employee_id", ts.get("employee_id", "")),
        "timesheet.period": ts.get("period", ""),
        "timesheet.total_hours": ts.get("total_hours", 0),
        "timesheet.status": ts.get("status", ""),
        "timesheet.timesheet_id": ts.get("timesheet_id", ""),
    }
    card_hash = build_card_hash(fields)
    return {
        "component_id": "ConfirmationCard",
        "props": {
            "title": "Approve Timesheet",
            "summary": f"Approve {emp.get('full_name', 'employee')}'s timesheet for {ts.get('period', '')}",
            "fields": fields,
            "capability_id": capability_id,
            "action_id": action_id,
            "voice_blocked": True,
            "card_hash": card_hash,
        },
        "card_hash": card_hash,
    }
