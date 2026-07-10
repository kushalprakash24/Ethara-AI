from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# --- EMPLOYEE SCHEMAS ---
class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    role: str

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: UUID
    joining_date: datetime

    class Config:
        from_attributes = True

# --- SEAT SCHEMAS ---
class SeatBase(BaseModel):
    seat_number: str
    status: str

class SeatResponse(SeatBase):
    id: UUID
    floor_id: UUID

    class Config:
        from_attributes = True

# --- ALLOCATION SCHEMAS ---
class AllocateSeatRequest(BaseModel):
    employee_id: UUID
    seat_id: UUID
    project_id: UUID

class AllocationResponse(BaseModel):
    id: UUID
    employee_id: UUID
    seat_id: UUID
    project_id: UUID
    allocated_at: datetime

    class Config:
        from_attributes = True