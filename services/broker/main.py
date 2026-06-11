from fastapi import FastAPI, HTTPException
import httpx
from broker.models import TokenExchangeRequest, TokenExchangeResponse
from broker.exchange import mint_token, MAX_TTL_SECONDS

app = FastAPI(title="Pangaea Token Broker", version="0.1.0")

_registry_client: httpx.AsyncClient | None = None

# Hardcoded fallback scopes for testing without live registry
_FALLBACK_SCOPES: dict[str, list[str]] = {
    "acme.timesheet": ["timesheet.read", "timesheet.submit", "timesheet.approve"],
    "acme.directory": ["directory.read", "directory.search"],
    "acme.permissions": ["permissions.check", "permissions.read"],
}


def configure(registry_client: httpx.AsyncClient | None = None):
    global _registry_client
    if registry_client is not None:
        _registry_client = registry_client


def reset():
    global _registry_client
    _registry_client = None


async def _get_manifest_scopes(capability_id: str) -> list[str]:
    if _registry_client:
        try:
            r = await _registry_client.get(f"/capabilities/{capability_id}/scopes")
            if r.status_code == 200:
                return r.json()["scopes"]
            if r.status_code == 404:
                raise HTTPException(404, f"Capability not registered: {capability_id!r}")
        except httpx.RequestError:
            pass
    scopes = _FALLBACK_SCOPES.get(capability_id)
    if scopes is None:
        raise HTTPException(404, f"Capability not found: {capability_id!r}")
    return scopes


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "broker"}


@app.post("/token/exchange", response_model=TokenExchangeResponse)
async def exchange_token(req: TokenExchangeRequest):
    """
    Mint a short-lived OBO token for exactly the requested scopes.
    INV-1: TTL ≤ 600s. Scopes must be ⊆ manifest scopes.
    """
    if not req.user_token or not req.user_token.startswith("Bearer "):
        raise HTTPException(401, "Invalid user token — must be a Bearer token")

    if req.ttl_seconds > MAX_TTL_SECONDS:
        raise HTTPException(
            403,
            f"Requested TTL {req.ttl_seconds}s exceeds maximum {MAX_TTL_SECONDS}s (INV-1)",
        )

    manifest_scopes = await _get_manifest_scopes(req.capability_id)

    forbidden = [s for s in req.required_scopes if s not in manifest_scopes]
    if forbidden:
        raise HTTPException(
            403,
            f"Requested scopes not in manifest for {req.capability_id!r}: {forbidden}",
        )

    user_sub = req.user_token.replace("Bearer ", "").strip()
    token = mint_token(
        capability_id=req.capability_id,
        scopes=req.required_scopes,
        user_sub=user_sub,
        ttl_seconds=req.ttl_seconds,
    )
    return TokenExchangeResponse(
        access_token=token,
        expires_in=req.ttl_seconds,
        capability_id=req.capability_id,
        scopes=req.required_scopes,
    )
