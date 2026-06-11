from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TimesheetStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Employee(BaseModel):
    employee_id: str
    full_name: str
    email: str
    team: str


class Timesheet(BaseModel):
    timesheet_id: str
    employee_id: str
    employee_name: str
    period: str
    total_hours: float
    status: TimesheetStatus
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None


class SubmitRequest(BaseModel):
    submitted_by: str


class ApproveRequest(BaseModel):
    approved_by: str
    timesheet_id: str
