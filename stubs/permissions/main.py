from fastapi import FastAPI, HTTPException
from permissions_models import PermissionCheckRequest, PermissionCheckResult, UserPermissions

app = FastAPI(title="Permissions Stub", version="1.0.0")

USER_ROLES: dict[str, list[str]] = {
    "E-10001": ["engineer"],
    "E-10002": ["engineer"],
    "E-10003": ["hr-specialist"],
    "E-10004": ["manager", "engineer"],
}

ROLE_PERMISSIONS: dict[str, dict[str, list[str]]] = {
    "manager": {
        "Timesheet": ["timesheet.read", "timesheet.approve"],
        "Employee": ["directory.read", "directory.search"],
    },
    "engineer": {
        "Timesheet": ["timesheet.read", "timesheet.submit"],
        "Employee": ["directory.read"],
    },
    "hr-specialist": {
        "Timesheet": ["timesheet.read", "timesheet.approve"],
        "Employee": ["directory.read", "directory.search"],
    },
}


def reset():
    pass  # stateless


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "permissions-stub"}


@app.get("/openapi.json", include_in_schema=False)
def openapi():
    return app.openapi()


@app.post("/permissions/check")
def check_permission(req: PermissionCheckRequest) -> PermissionCheckResult:
    roles = USER_ROLES.get(req.user_id, [])
    allowed = False
    for role in roles:
        role_perms = ROLE_PERMISSIONS.get(role, {})
        resource_perms = role_perms.get(req.resource_type, [])
        if req.action in resource_perms:
            allowed = True
            break
    return PermissionCheckResult(
        allowed=allowed,
        user_id=req.user_id,
        action=req.action,
        resource_type=req.resource_type,
        reason="role-based" if allowed else "no matching role permission",
    )


@app.get("/permissions/user/{user_id}")
def get_user_permissions(user_id: str) -> UserPermissions:
    roles = USER_ROLES.get(user_id)
    if roles is None:
        raise HTTPException(status_code=404, detail="User not found")
    capabilities: list[str] = []
    for role in roles:
        role_perms = ROLE_PERMISSIONS.get(role, {})
        for resource_perms in role_perms.values():
            capabilities.extend(p for p in resource_perms if p not in capabilities)
    return UserPermissions(user_id=user_id, roles=roles, capabilities=capabilities)
