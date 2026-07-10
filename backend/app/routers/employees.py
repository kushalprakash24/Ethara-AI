from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from .. import models

router = APIRouter(prefix="/employees", tags=["Employee Management"])

@router.delete("/offboard/{employee_id}", status_code=status.HTTP_200_OK)
def offboard_employee(employee_id: UUID, db: Session = Depends(get_db)):
    """
    Offboards an employee by freeing up their desk allocation 
    and deleting their corporate profile cleanly.
    """
    # 1. Verify Employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found in database registry.")

    # 2. Check if they have an active seat allocation
    allocation = db.query(models.SeatAllocation).filter(models.SeatAllocation.employee_id == employee_id).first()
    if allocation:
        # Mark the physical seat back to vacant
        seat = db.query(models.Seat).filter(models.Seat.id == allocation.seat_id).first()
        if seat:
            seat.status = "vacant"
        # Delete the seat mapping bridge record
        db.delete(allocation)

    # 3. Safely delete the core employee profile row
    db.delete(employee)
    db.commit()

    return {"status": "success", "message": f"Successfully offboarded {employee.name} and vacated their desk."}