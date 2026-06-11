from pydantic import BaseModel, Field
from typing import Optional


class TokenExchangeRequest(BaseModel):
    user_token: str
    capability_id: str
    required_scopes: list[str]
    ttl_seconds: int = 300


class TokenExchangeResponse(BaseModel):
    access_token: str
    expires_in: int
    capability_id: str
    scopes: list[str]
    token_type: str = "Bearer"
