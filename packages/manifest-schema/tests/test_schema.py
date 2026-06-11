"""Manifest schema validation tests — Phase 0 gate."""
import os
import json
import copy
import yaml
import jsonschema
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
STUBS_DIR = os.path.join(ROOT, "stubs")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "capability.schema.json")


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_stub_manifest(stub_dir):
    path = os.path.join(STUBS_DIR, stub_dir, "capability.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _validate(manifest_dict, schema_dict):
    jsonschema.validate(manifest_dict, schema_dict)


def _validate_fails(manifest_dict, schema_dict) -> bool:
    try:
        jsonschema.validate(manifest_dict, schema_dict)
        return False
    except jsonschema.ValidationError:
        return True


# ── Valid manifests pass ────────────────────────────────────────────────────

def test_valid_timesheet_manifest(schema):
    """Phase 0: valid timesheet manifest passes schema."""
    _validate(load_stub_manifest("timesheet"), schema)


def test_valid_people_manifest(schema):
    """Phase 0: valid people-data manifest passes schema."""
    _validate(load_stub_manifest("people-data"), schema)


def test_valid_permissions_manifest(schema):
    """Phase 0: valid permissions manifest passes schema."""
    _validate(load_stub_manifest("permissions"), schema)


# ── Required field enforcement ──────────────────────────────────────────────

def test_missing_manifest_version_fails(schema):
    """Schema rejects manifests missing the manifest version field."""
    bad = load_stub_manifest("timesheet")
    del bad["manifest"]
    assert _validate_fails(bad, schema)


def test_missing_capability_id_fails(schema):
    """Schema rejects manifests missing capability.id."""
    bad = load_stub_manifest("timesheet")
    del bad["capability"]["id"]
    assert _validate_fails(bad, schema)


def test_bad_lifecycle_value_fails(schema):
    """Schema rejects unknown lifecycle values."""
    bad = load_stub_manifest("timesheet")
    bad["capability"]["lifecycle"] = "production"
    assert _validate_fails(bad, schema)


def test_bad_risk_tier_fails(schema):
    """Schema rejects unknown risk tier values."""
    bad = load_stub_manifest("timesheet")
    bad["actions"][0]["risk"] = "medium"
    assert _validate_fails(bad, schema)


def test_empty_fulfillment_modes_fails(schema):
    """Schema requires at least one fulfillment mode."""
    bad = load_stub_manifest("timesheet")
    bad["runtime"]["fulfillment_modes"] = []
    assert _validate_fails(bad, schema)


def test_consequential_without_confirmation_fails(schema):
    """INV-5: consequential action without confirmation block fails schema."""
    bad = load_stub_manifest("timesheet")
    for action in bad["actions"]:
        if action["risk"] == "consequential":
            del action["confirmation"]
    assert _validate_fails(bad, schema)


def test_bad_id_format_fails(schema):
    """Schema enforces reverse-DNS id format."""
    bad = load_stub_manifest("timesheet")
    bad["capability"]["id"] = "TimesheetService"
    assert _validate_fails(bad, schema)


def test_empty_scopes_fails(schema):
    """Schema requires at least one auth scope."""
    bad = load_stub_manifest("timesheet")
    bad["auth"]["scopes"] = []
    assert _validate_fails(bad, schema)


def test_missing_entities_fails(schema):
    """Schema requires entities array."""
    bad = load_stub_manifest("timesheet")
    del bad["entities"]
    assert _validate_fails(bad, schema)


def test_missing_intents_fails(schema):
    """Schema requires intents array."""
    bad = load_stub_manifest("timesheet")
    del bad["intents"]
    assert _validate_fails(bad, schema)
