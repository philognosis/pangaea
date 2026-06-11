from pydantic import BaseModel, Field
from typing import Any, Optional
import uuid


class PushEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    capability_id: str
    timesheet_id: str
    triggered_by: Optional[str] = None


class ApproveRequest(BaseModel):
    timesheet_id: str
    user_token: str
    user_sub: str
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
