from pydantic import BaseModel
from typing import Optional


class Team(BaseModel):
    team_id: str
    name: str
    manager_id: str


class Employee(BaseModel):
    employee_id: str
    full_name: str
    email: str
    team_id: str
    team_name: str
    role: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None


class EmployeeSearchResult(BaseModel):
    employees: list[Employee]
    total: int
