from fastapi import FastAPI
from router.models import RouteRequest, RouteResult, ClarificationNeeded, RegisterCapabilityRequest
from router.scorer import Router

app = FastAPI(title="Pangaea Router", version="0.1.0")
router = Router()

# Seed with timesheet intents for PoC
router.register_capability("acme.timesheet", [
    {
        "id": "approve_timesheet",
        "utterances": [
            "approve timesheet for {employee}",
            "approve {employee}'s timesheet",
            "sign off on {employee}'s hours",
            "approve hours for {employee}",
        ],
    },
    {
        "id": "submit_timesheet",
        "utterances": [
            "submit my timesheet",
            "submit timesheet for {period}",
            "send my hours for approval",
        ],
    },
])
router.register_capability("acme.directory", [
    {
        "id": "find_employee",
        "utterances": [
            "find {employee}",
            "look up {employee}",
            "who is {employee}",
            "search for {employee}",
        ],
    },
])


def reset():
    router.reset()
    # Re-seed after reset
    router.register_capability("acme.timesheet", [
        {"id": "approve_timesheet", "utterances": ["approve timesheet for {employee}", "approve {employee}'s timesheet"]},
        {"id": "submit_timesheet", "utterances": ["submit my timesheet", "submit timesheet for {period}"]},
    ])
    router.register_capability("acme.directory", [
        {"id": "find_employee", "utterances": ["find {employee}", "look up {employee}"]},
    ])


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "router"}


@app.post("/route")
def route_intent(req: RouteRequest):
    result = router.route(req.utterance)
    if isinstance(result, RouteResult):
        return {"routed": True, "result": result.model_dump()}
    return {"routed": False, "clarification": result.model_dump()}


@app.post("/register")
def register_capability(req: RegisterCapabilityRequest):
    router.register_capability(req.capability_id, req.intents)
    return {"registered": req.capability_id}


@app.get("/hot_paths")
def get_hot_paths():
    return {"count": len(router._hot_paths)}
