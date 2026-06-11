"""
HMAC-SHA256 JWT implementation using stdlib only.
(python-jose/cryptography skipped: Rust binary unavailable in this env)

INV-1: No standing credentials. TTL ≤ 600s enforced here.
"""
import hmac
import hashlib
import base64
import json
import time

MAX_TTL_SECONDS = 600
JWT_SECRET = "pangaea-dev-secret-change-in-prod"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def mint_token(capability_id: str, scopes: list[str], user_sub: str, ttl_seconds: int) -> str:
    """Mint a short-lived HS256 JWT scoped to exactly the requested capability and scopes."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": "pangaea-broker",
        "sub": user_sub,
        "aud": capability_id,
        "iat": now,
        "exp": now + ttl_seconds,
        "scopes": scopes,
        "capability_id": capability_id,
    }
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    msg = f"{h}.{p}".encode()
    sig = hmac.new(JWT_SECRET.encode(), msg, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def decode_token(token: str) -> dict:
    """Decode and verify an HS256 JWT. Raises ValueError on invalid token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    h, p, sig = parts
    msg = f"{h}.{p}".encode()
    expected_sig = hmac.new(JWT_SECRET.encode(), msg, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected_sig), sig):
        raise ValueError("Invalid JWT signature")
    payload = json.loads(_b64url_decode(p))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("JWT expired")
    return payload
