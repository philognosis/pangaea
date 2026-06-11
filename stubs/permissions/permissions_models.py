from pydantic import BaseModel
from typing import Optional


class PermissionCheckRequest(BaseModel):
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None


class PermissionCheckResult(BaseModel):
    allowed: bool
    user_id: str
    action: str
    resource_type: str
    reason: str


class UserPermissions(BaseModel):
    user_id: str
    roles: list[str]
    capabilities: list[str]
