import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, ROOT)

import pytest
import yaml
import jsonschema
import json


SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "capability.schema.json"
)


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate(manifest_dict, schema_dict):
    jsonschema.validate(manifest_dict, schema_dict)


def validate_fails(manifest_dict, schema_dict):
    try:
        jsonschema.validate(manifest_dict, schema_dict)
        return False
    except jsonschema.ValidationError:
        return True
