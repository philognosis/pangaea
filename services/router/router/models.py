from pydantic import BaseModel
from typing import Optional, Any


class RouteResult(BaseModel):
    capability_id: str
    intent_id: str
    confidence: float
    slots: dict[str, Any] = {}
    compiled: bool = False


class ClarificationNeeded(BaseModel):
    needs_clarification: bool = True
    question: str
    partial_matches: list[str] = []


class RouteRequest(BaseModel):
    utterance: str
    user_context: Optional[dict[str, Any]] = None


class RegisterCapabilityRequest(BaseModel):
    capability_id: str
    intents: list[dict[str, Any]]
