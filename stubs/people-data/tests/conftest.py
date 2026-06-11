import sys
import os
import importlib.util

_stub_dir = os.path.dirname(os.path.dirname(__file__))
if _stub_dir not in sys.path:
    sys.path.insert(0, _stub_dir)

_spec = importlib.util.spec_from_file_location("pd_stub_main_unit", os.path.join(_stub_dir, "main.py"))
pd_main = importlib.util.module_from_spec(_spec)
sys.modules["pd_stub_main_unit"] = pd_main
_spec.loader.exec_module(pd_main)

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def reset_state():
    pd_main.reset()
    yield


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=pd_main.app), base_url="http://test") as c:
        yield c
