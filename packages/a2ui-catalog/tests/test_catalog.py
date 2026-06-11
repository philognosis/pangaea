"""A2UI catalog validation tests — Phase 1 component contract."""
import pytest
from pydantic import ValidationError
from catalog import render_from_json, CATALOG


# ── Valid renders ───────────────────────────────────────────────────────────

def test_action_card_valid_props():
    """ActionCard renders from valid JSON props."""
    props = render_from_json("ActionCard", {
        "title": "Timesheet Ready",
        "body": "Alice's timesheet for 2025-W24 awaits approval.",
        "entity_id": "TS-001",
        "entity_type": "Timesheet",
        "capability_id": "acme.timesheet",
        "actions": [{"label": "Approve", "intent": "approve_timesheet_action", "style": "primary"}],
    })
    assert props.title == "Timesheet Ready"
    assert props.capability_id == "acme.timesheet"


def test_confirmation_card_valid_props():
    """ConfirmationCard renders from resolved entity data (INV-4)."""
    props = render_from_json("ConfirmationCard", {
        "title": "Approve Timesheet",
        "summary": "Approve Alice Smith's timesheet for 2025-W24",
        "fields": {
            "employee.full_name": "Alice Smith",
            "employee.employee_id": "E-10001",
            "timesheet.period": "2025-W24",
            "timesheet.total_hours": 40.0,
        },
        "capability_id": "acme.timesheet",
        "action_id": "approve_timesheet_action",
        "voice_blocked": True,
    })
    assert props.voice_blocked is True
    assert props.fields["employee.full_name"] == "Alice Smith"


def test_entity_card_valid_props():
    """EntityCard renders from valid entity data."""
    props = render_from_json("EntityCard", {
        "entity_id": "E-10001",
        "entity_type": "Employee",
        "display_name": "Alice Smith",
        "fields": {"email": "alice@acme.com", "team": "Engineering"},
        "capability_id": "acme.directory",
    })
    assert props.entity_id == "E-10001"


def test_data_table_valid_props():
    """DataTable renders from valid tabular data."""
    props = render_from_json("DataTable", {
        "columns": [{"key": "name", "label": "Name", "sortable": True}],
        "rows": [{"name": "Alice Smith"}],
        "total": 1,
    })
    assert props.total == 1
    assert props.columns[0].key == "name"


def test_status_badge_valid_props():
    """StatusBadge renders from valid status data."""
    props = render_from_json("StatusBadge", {
        "status": "submitted",
        "label": "Submitted",
        "variant": "warning",
    })
    assert props.status == "submitted"


# ── Unknown component raises ────────────────────────────────────────────────

def test_render_unknown_component_raises():
    """INV-2: unknown component ID must raise — no escape hatch."""
    with pytest.raises(ValueError, match="Unknown component ID"):
        render_from_json("ArbitraryWidget", {"html": "<script>alert(1)</script>"})


# ── Invalid props raise ─────────────────────────────────────────────────────

def test_render_invalid_props_raises():
    """INV-2: schema-invalid props raise ValidationError."""
    with pytest.raises(ValidationError):
        render_from_json("ActionCard", {
            "title": "Missing required fields",
            # missing: body, capability_id
        })


def test_catalog_has_ten_components():
    """A2UI catalog registers all 10 required components."""
    required = {
        "ActionCard", "ConfirmationCard", "EntityCard", "EntityPicker",
        "DataTable", "StatusBadge", "SectionHeader", "CompositeLayout", "ReceiptView",
    }
    assert required.issubset(set(CATALOG.keys()))
