import sys
import os
import importlib.util

_svc_dir = os.path.dirname(os.path.dirname(__file__))
if _svc_dir not in sys.path:
    sys.path.insert(0, _svc_dir)

_spec = importlib.util.spec_from_file_location("broker_svc_main", os.path.join(_svc_dir, "main.py"))
broker_main = importlib.util.module_from_spec(_spec)
sys.modules["broker_svc_main"] = broker_main
_spec.loader.exec_module(broker_main)

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def reset_state():
    broker_main.reset()
    yield


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=broker_main.app), base_url="http://test") as c:
        yield c
