import sys
import os
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def load_stub(stub_dir: str, alias: str):
    """Load a stub's main.py with a unique module alias to avoid cache collisions."""
    stub_path = os.path.join(ROOT, "stubs", stub_dir)
    if stub_path not in sys.path:
        sys.path.insert(0, stub_path)
    main_file = os.path.join(stub_path, "main.py")
    spec = importlib.util.spec_from_file_location(alias, main_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


import pytest
from httpx import AsyncClient, ASGITransport

ts_mod = load_stub("timesheet", "ts_stub_main")
pd_mod = load_stub("people-data", "pd_stub_main")
perm_mod = load_stub("permissions", "perm_stub_main")


@pytest.fixture(autouse=True)
def reset_all():
    ts_mod.reset()
    pd_mod.reset()
    perm_mod.reset()
    yield


@pytest.fixture
async def ts_client():
    async with AsyncClient(transport=ASGITransport(app=ts_mod.app), base_url="http://timesheet") as c:
        yield c


@pytest.fixture
async def pd_client():
    async with AsyncClient(transport=ASGITransport(app=pd_mod.app), base_url="http://people") as c:
        yield c


@pytest.fixture
async def perm_client():
    async with AsyncClient(transport=ASGITransport(app=perm_mod.app), base_url="http://permissions") as c:
        yield c
