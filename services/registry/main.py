from fastapi import FastAPI
from typing import Optional
from registry.models import PublishRequest, PublishResponse, CapabilityRecord
from registry.store import CapabilityStore

app = FastAPI(title="Pangaea Registry", version="0.1.0")
store = CapabilityStore()


def reset():
    store.reset()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "registry"}


@app.post("/capabilities", response_model=PublishResponse)
def publish_capability(req: PublishRequest):
    """Register or update a capability manifest. Runs composition checks."""
    record = store.publish(req)
    return PublishResponse(
        id=record.id,
        name=record.name,
        version=record.version,
        lifecycle=record.lifecycle,
        published_at=record.published_at,
    )


@app.get("/capabilities")
def list_capabilities(lifecycle: Optional[str] = None):
    records = store.list_all(lifecycle=lifecycle)
    return {"capabilities": [r.model_dump() for r in records], "total": len(records)}


@app.get("/capabilities/{cap_id}")
def get_capability(cap_id: str):
    record = store.get(cap_id)
    return record.model_dump()


@app.delete("/capabilities/{cap_id}")
def delete_capability(cap_id: str):
    store.delete(cap_id)
    return {"deleted": cap_id}


@app.get("/capabilities/{cap_id}/scopes")
def get_capability_scopes(cap_id: str):
    scopes = store.get_manifest_scopes(cap_id)
    return {"capability_id": cap_id, "scopes": scopes}
