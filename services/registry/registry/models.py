from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone


class CapabilityRecord(BaseModel):
    id: str
    name: str
    version: str
    lifecycle: str
    manifest: dict[str, Any]
    owner_team: str
    published_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_healthy_at: Optional[str] = None


class PublishRequest(BaseModel):
    manifest: dict[str, Any]


class PublishResponse(BaseModel):
    id: str
    name: str
    version: str
    lifecycle: str
    published_at: str
