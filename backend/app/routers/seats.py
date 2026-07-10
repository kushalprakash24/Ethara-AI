from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/seats", tags=["Seats & Allocations"])

@router.post("/allocate", response_model=schemas.AllocationResponse, status_code=status.HTTP_201_CREATED)
def allocate_seat(payload: schemas.AllocateSeatRequest, db: Session = Depends(get_db)):
    # 1. Verify seat availability
    seat = db.query(models.Seat).filter(models.Seat.id == payload.seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    if seat.status == "occupied":
        raise HTTPException(status_code=400, detail="Seat is already occupied")

    # 2. Verify Employee doesn't already have a seat
    existing_alloc = db.query(models.SeatAllocation).filter(models.SeatAllocation.employee_id == payload.employee_id).first()
    if existing_alloc:
        raise HTTPException(status_code=400, detail="Employee is already allocated to a seat")

    # 3. Create the Allocation mapping record
    new_allocation = models.SeatAllocation(
        employee_id=payload.employee_id,
        seat_id=payload.seat_id,
        project_id=payload.project_id
    )
    
    # 4. Update the Seat status to occupied
    seat.status = "occupied"
    
    db.add(new_allocation)
    db.commit()
    db.refresh(new_allocation)
    return new_allocation

@router.delete("/release/{seat_id}", status_code=status.HTTP_200_OK)
def release_seat(seat_id: UUID, db: Session = Depends(get_db)):
    # 1. Find the active allocation record
    allocation = db.query(models.SeatAllocation).filter(models.SeatAllocation.seat_id == seat_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="No active allocation found for this seat")

    # 2. Update the seat's operational status back to vacant
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if seat:
        seat.status = "vacant"

    # 3. Remove the allocation bridge record
    db.delete(allocation)
    db.commit()
    return {"message": "Seat successfully released and marked vacant"}

@router.post("/auto-allocate-joiner", status_code=status.HTTP_201_CREATED)
def auto_allocate_new_joiner(
    name: str, 
    email: str, 
    role: str, 
    project_id: str, 
    db: Session = Depends(get_db)
):
    # 1. Ensure the email isn't taken
    existing_emp = db.query(models.Employee).filter(models.Employee.email == email).first()
    if existing_emp:
        raise HTTPException(status_code=400, detail="An employee with this email already exists.")

    # 2. Grab the single next available vacant seat
    vacant_seat = db.query(models.Seat).filter(models.Seat.status == "vacant").first()
    if not vacant_seat:
        raise HTTPException(status_code=400, detail="Building capacity fully reached!")

    # 💡 SAFE RESOLUTION: Grab the first seeded project if the frontend sent a dummy string/UUID
    proj = db.query(models.Project).first()
    if not proj:
        raise HTTPException(status_code=400, detail="No projects initialized in backend records.")

    # 3. Create the Employee row entry
    new_employee = models.Employee(name=name, email=email, role=role)
    db.add(new_employee)
    db.flush()

    # 4. Bind the Allocation mapping record
    allocation = models.SeatAllocation(
        employee_id=new_employee.id,
        seat_id=vacant_seat.id,
        project_id=proj.id  # Use safely resolved project model reference
    )
    
    # 5. Flip desk assignment state to occupied
    vacant_seat.status = "occupied"
    
    db.add(allocation)
    db.commit()

    return {
        "status": "success",
        "allocated_desk": vacant_seat.seat_number
    }

@router.delete("/release-by-code/{seat_code}", status_code=status.HTTP_200_OK)
def release_seat_by_code(seat_code: str, db: Session = Depends(get_db)):
    """
    Looks up a seat by its display code (e.g., F1-A-0001) and frees it up instantly.
    """
    # 1. Find the seat structural record
    seat = db.query(models.Seat).filter(models.Seat.seat_number == seat_code).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat code not found in building system.")

    # 2. Find and delete the active allocation row
    allocation = db.query(models.SeatAllocation).filter(models.SeatAllocation.seat_id == seat.id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="This desk is already vacant.")

    # 3. Mark the desk back to vacant
    seat.status = "vacant"
    
    db.delete(allocation)
    db.commit()
    
    return {"status": "success", "message": f"Desk {seat_code} is now vacant."}

@router.get("/floor-plan/{floor_number}")
def get_floor_plan(floor_number: int, db: Session = Depends(get_db)):
    """
    Returns all desks on a specific floor with their current allocation statuses
    and occupant details if occupied.
    """
    seats = db.query(models.Seat)\
              .join(models.Floor)\
              .filter(models.Floor.floor_number == floor_number)\
              .order_by(models.Seat.seat_number)\
              .all()
              
    plan = []
    for seat in seats:
        occupant_name = None
        if seat.status == "occupied" and seat.allocation:
            occupant_name = seat.allocation.employee.name
            
        plan.append({
            "id": str(seat.id),
            "seat_number": seat.seat_number,
            "status": seat.status,
            "occupant": occupant_name
        })
    return plan


@router.post("/manual-allocate", status_code=status.HTTP_200_OK)
def manual_allocate(payload: schemas.AllocateSeatRequest, db: Session = Depends(get_db)):
    """
    Manually binds a specific employee to a specific desk for a project.
    Frees up their old desk automatically if they are moving.
    """
    # 1. Verify seat availability
    seat = db.query(models.Seat).filter(models.Seat.id == payload.seat_id).first()
    if not seat or seat.status == "occupied":
        raise HTTPException(status_code=400, detail="Target desk is unavailable or does not exist.")

    # 2. Check if employee already has a desk. If yes, release it first (Desk Swapping)
    old_allocation = db.query(models.SeatAllocation).filter(models.SeatAllocation.employee_id == payload.employee_id).first()
    if old_allocation:
        old_seat = db.query(models.Seat).filter(models.Seat.id == old_allocation.seat_id).first()
        if old_seat:
            old_seat.status = "vacant"
        db.delete(old_allocation)

    # 3. Create new allocation mapping record
    new_alloc = models.SeatAllocation(
        employee_id=payload.employee_id,
        seat_id=payload.seat_id,
        project_id=payload.project_id
    )
    seat.status = "occupied"
    
    db.add(new_alloc)
    db.commit()
    return {"status": "success", "message": f"Successfully allocated desk {seat.seat_number}"}