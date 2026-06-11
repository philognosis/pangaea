"""
E2E test conftest — wires all services together using ASGI transport.
No real network calls; all services run in-process.
"""
import sys
import os
import importlib.util
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def load_service(rel_path: str, alias: str):
    """Load a service's main.py with a unique module alias."""
    full_dir = os.path.join(ROOT, rel_path)
    if full_dir not in sys.path:
        sys.path.insert(0, full_dir)
    main_file = os.path.join(full_dir, "main.py")
    spec = importlib.util.spec_from_file_location(alias, main_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# Load all service modules with unique aliases
ts_mod = load_service("stubs/timesheet", "e2e_ts_main")
reg_mod = load_service("services/registry", "e2e_reg_main")
broker_mod = load_service("services/broker", "e2e_broker_main")
gw_mod = load_service("services/gateway", "e2e_gw_main")


@pytest.fixture(scope="module")
async def e2e(request):
    """
    Module-scoped fixture: creates all service clients and wires them together.
    State flows across tests in order — this models the real push→approve flow.
    """
    # Reset all service state
    ts_mod.reset()
    reg_mod.reset()
    broker_mod.reset()
    gw_mod.reset()

    async with (
        AsyncClient(transport=ASGITransport(app=ts_mod.app), base_url="http://timesheet") as ts,
        AsyncClient(transport=ASGITransport(app=reg_mod.app), base_url="http://registry") as reg,
        AsyncClient(transport=ASGITransport(app=broker_mod.app), base_url="http://broker") as broker,
        AsyncClient(transport=ASGITransport(app=gw_mod.app), base_url="http://gateway") as gw,
    ):
        # Wire services: gateway calls timesheet stub and broker
        gw_mod.configure(timesheet_client=ts, broker_client=broker)
        # Wire broker to registry for scope lookup
        broker_mod.configure(registry_client=reg)

        # Register the timesheet capability in the registry
        await reg.post("/capabilities", json={"manifest": {
            "manifest": "0.1",
            "capability": {
                "id": "acme.timesheet",
                "name": "Timesheet Management",
                "description": "Submit and approve timesheets",
                "owner": "payroll-team",
                "lifecycle": "ga",
                "version": "1.0.0",
            },
            "runtime": {
                "base_url": "http://timesheet",
                "health_url": "/healthz",
                "fulfillment_modes": ["direct"],
            },
            "auth": {
                "idp": "keycloak",
                "audience": "timesheet-service",
                "scopes": ["timesheet.read", "timesheet.submit", "timesheet.approve"],
            },
            "entities": [{"type": "Timesheet", "owns": True}],
            "intents": [{
                "id": "approve_timesheet",
                "description": "Approve a timesheet",
                "utterances": ["approve timesheet for {employee}"],
            }],
            "actions": [{
                "id": "approve_timesheet_action",
                "risk": "consequential",
                "confirmation": {
                    "template": "Approve timesheet for {{employee.full_name}}",
                    "show_fields": ["employee.full_name"],
                    "requires": ["explicit_tap"],
                    "voice_blocked": True,
                },
            }],
        }})

        yield {"ts": ts, "reg": reg, "broker": broker, "gw": gw}
