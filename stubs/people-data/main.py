from fastapi import FastAPI, HTTPException
from typing import Optional
from people_models import Employee, Team, EmployeeSearchResult

app = FastAPI(title="People Data Stub", version="1.0.0")

TEAMS: dict[str, Team] = {
    "T-001": Team(team_id="T-001", name="Engineering", manager_id="E-10004"),
    "T-002": Team(team_id="T-002", name="HR", manager_id="E-10003"),
}

EMPLOYEES: dict[str, Employee] = {
    "E-10001": Employee(
        employee_id="E-10001", full_name="Alice Smith", email="alice@acme.com",
        team_id="T-001", team_name="Engineering", role="engineer",
        manager_id="E-10004", manager_name="Diana Prince",
    ),
    "E-10002": Employee(
        employee_id="E-10002", full_name="Bob Jones", email="bob@acme.com",
        team_id="T-001", team_name="Engineering", role="engineer",
        manager_id="E-10004", manager_name="Diana Prince",
    ),
    "E-10003": Employee(
        employee_id="E-10003", full_name="Carol White", email="carol@acme.com",
        team_id="T-002", team_name="HR", role="hr-specialist",
    ),
    "E-10004": Employee(
        employee_id="E-10004", full_name="Diana Prince", email="diana@acme.com",
        team_id="T-001", team_name="Engineering", role="manager",
    ),
}


def reset():
    pass  # seed data is immutable


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "people-data-stub"}


@app.get("/openapi.json", include_in_schema=False)
def openapi():
    return app.openapi()


@app.get("/employees")
def list_employees(team_id: Optional[str] = None, role: Optional[str] = None):
    employees = list(EMPLOYEES.values())
    if team_id:
        employees = [e for e in employees if e.team_id == team_id]
    if role:
        employees = [e for e in employees if e.role == role]
    return EmployeeSearchResult(employees=employees, total=len(employees))


@app.get("/employees/search")
def search_employees(q: str = ""):
    results = [e for e in EMPLOYEES.values() if q.lower() in e.full_name.lower() or q.lower() in e.email.lower()]
    return EmployeeSearchResult(employees=results, total=len(results))


@app.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@app.get("/teams")
def list_teams():
    return {"teams": [t.model_dump() for t in TEAMS.values()]}


@app.get("/teams/{team_id}")
def get_team(team_id: str):
    team = TEAMS.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
