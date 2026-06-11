import sys
import os
import importlib.util

_svc_dir = os.path.dirname(os.path.dirname(__file__))
if _svc_dir not in sys.path:
    sys.path.insert(0, _svc_dir)

_spec = importlib.util.spec_from_file_location("reg_svc_main", os.path.join(_svc_dir, "main.py"))
reg_main = importlib.util.module_from_spec(_spec)
sys.modules["reg_svc_main"] = reg_main
_spec.loader.exec_module(reg_main)

import pytest
from httpx import AsyncClient, ASGITransport


TIMESHEET_MANIFEST = {
    "manifest": "0.1",
    "capability": {
        "id": "acme.timesheet",
        "name": "Timesheet Management",
        "description": "Submit and approve timesheets",
        "owner": "payroll-team",
        "lifecycle": "ga",
        "version": "1.0.0",
    },
    "runtime": {"base_url": "http://localhost:8101", "health_url": "/healthz", "fulfillment_modes": ["direct"]},
    "auth": {"idp": "keycloak", "audience": "timesheet-service", "scopes": ["timesheet.read", "timesheet.approve"]},
    "entities": [{"type": "Timesheet", "owns": True}],
    "intents": [{"id": "approve_timesheet", "description": "Approve a timesheet", "utterances": ["approve timesheet for {employee}"]}],
    "actions": [
        {
            "id": "approve_timesheet_action",
            "risk": "consequential",
            "confirmation": {
                "template": "Approve timesheet for {{employee.full_name}}",
                "show_fields": ["employee.full_name"],
                "requires": ["explicit_tap"],
                "voice_blocked": True,
            },
        }
    ],
}

DIRECTORY_MANIFEST = {
    "manifest": "0.1",
    "capability": {
        "id": "acme.directory",
        "name": "People Directory",
        "description": "Employee directory",
        "owner": "hr-team",
        "lifecycle": "ga",
        "version": "1.0.0",
    },
    "runtime": {"base_url": "http://localhost:8102", "health_url": "/healthz", "fulfillment_modes": ["direct"]},
    "auth": {"idp": "keycloak", "audience": "directory-service", "scopes": ["directory.read"]},
    "entities": [{"type": "Employee", "owns": True}, {"type": "Team", "owns": True}],
    "intents": [{"id": "find_employee", "description": "Find an employee", "utterances": ["find {employee}"]}],
    "actions": [{"id": "get_employee", "risk": "read"}],
}


@pytest.fixture(autouse=True)
def reset_state():
    reg_main.reset()
    yield


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=reg_main.app), base_url="http://test") as c:
        yield c
