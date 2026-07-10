from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, Integer, case
from pydantic import BaseModel
from typing import Optional, List, Dict
from ..database import get_db
from .. import models

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Search"])

# 📋 input validation ke liye Pydantic Schema (New Joiner Form ke liye)
class SeatAllocationRequest(BaseModel):
    employee_name: str
    employee_email: str
    role: str
    project_name: str
    seat_number: str  # Frontend se seat number (jaise 'F3-A-0466') input lene ke liye

@router.get("/search")
def search_directory(
    q: Optional[str] = Query(None, description="Search by employee name or email"),
    project_id: Optional[str] = Query(None, description="Filter by Project UUID"),
    floor_id: Optional[str] = Query(None, description="Filter by Floor UUID"),
    role: Optional[str] = Query(None, description="Filter by employee role"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    High-speed corporate directory lookup handling text queries and relational filters.
    """
    query = db.query(
        models.Employee.id.label("employee_id"),
        models.Employee.name.label("employee_name"),
        models.Employee.email.label("employee_email"),
        models.Employee.role.label("employee_role"),
        models.Seat.id.label("seat_id"),          # Frontend actions ke liye seat_id zaroori h
        models.Seat.seat_number.label("seat_number"),
        models.Floor.floor_number.label("floor_number"),
        models.Project.name.label("project_name")
    ).outerjoin(models.SeatAllocation, models.Employee.id == models.SeatAllocation.employee_id)\
     .outerjoin(models.Seat, models.SeatAllocation.seat_id == models.Seat.id)\
     .outerjoin(models.Floor, models.Seat.floor_id == models.Floor.id)\
     .outerjoin(models.Project, models.SeatAllocation.project_id == models.Project.id)

    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            or_(
                models.Employee.name.ilike(search_filter),
                models.Employee.email.ilike(search_filter)
            )
        )

    if project_id:
        query = query.filter(models.SeatAllocation.project_id == project_id)
    if floor_id:
        query = query.filter(models.Seat.floor_id == floor_id)
    if role:
        query = query.filter(models.Employee.role == role)

    total_count = query.count()
    results = query.offset(offset).limit(limit).all()

    data = [dict(row._mapping) for row in results]

    return {
        "total_matches": total_count,
        "limit": limit,
        "offset": offset,
        "results": data
    }


@router.get("/metrics")
def get_utilization_metrics(db: Session = Depends(get_db)):
    """
    Computes system-wide operational metrics for frontend charts.
    """
    total_seats = db.query(models.Seat).count()
    occupied_seats = db.query(models.Seat).filter(models.Seat.status == "occupied").count()
    vacant_seats = db.query(models.Seat).filter(models.Seat.status == "vacant").count()
    
    utilization_rate = round((occupied_seats / total_seats) * 100, 2) if total_seats > 0 else 0
    
    floor_stats = db.query(
        models.Floor.floor_number,
        models.Floor.block_name,
        func.count(models.Seat.id).label("total_desks"),
        func.sum(case((models.Seat.status == 'occupied', 1), else_=0)).label("occupied_desks")  
    ).join(models.Seat, models.Floor.id == models.Seat.floor_id).group_by(models.Floor.id).all()

    floor_distribution = [
        {
            "floor": row.floor_number,
            "block": row.block_name,
            "total": row.total_desks,
            "occupied": row.occupied_desks or 0,
            "vacancy": row.total_desks - (row.occupied_desks or 0)
        }
        for row in floor_stats
    ]

    return {
        "summary": {
            "total_structural_capacity": total_seats,
            "allocated_seats": occupied_seats,
            "available_seats": vacant_seats,
            "global_utilization_rate": f"{utilization_rate}%"
        },
        "floor_breakdown": floor_distribution
    }


# ➕ 1. NEW JOINER ALLOCATION ENDPOINT
@router.post("/allocate")
def allocate_new_joiner(payload: SeatAllocationRequest, db: Session = Depends(get_db)):
    # Check karein ki seat database me exist karti h ya nahi
    seat = db.query(models.Seat).filter(models.Seat.seat_number == payload.seat_number).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Specified seat number not found")
    
    # Check karein ki seat pehle se occupied toh nahi h
    if seat.status == "occupied":
        raise HTTPException(status_code=400, detail="This seat is already occupied")

    # Pehle Naya Employee register karein
    new_employee = models.Employee(
        name=payload.employee_name,
        email=payload.employee_email,
        role=payload.role
    )
    db.add(new_employee)
    db.flush() # Employee ID generate karne ke liye temporary save

    # Project dhoondein ya default assign karein
    project = db.query(models.Project).filter(models.Project.name.ilike(f"%{payload.project_name}%")).first()
    project_id = project.id if project else None

    # Seat allocation mapping table update karein aur seat status occupied karein
    new_allocation = models.SeatAllocation(
        employee_id=new_employee.id,
        seat_id=seat.id,
        project_id=project_id
    )
    db.add(new_allocation)
    
    # Seat table me status change karein
    seat.status = "occupied"
    
    db.commit()
    return {"status": "success", "message": f"Successfully allocated seat {seat.seat_number} to {new_employee.name}"}


# 🗑️ 2. SEAT RELEASE ENDPOINT (Vacate/Khali karne ke liye)
@router.put("/release/{seat_id}")
def release_seat(seat_id: str, db: Session = Depends(get_db)):
    # Seat allocation dhoondein
    allocation = db.query(models.SeatAllocation).filter(models.SeatAllocation.seat_id == seat_id).first()
    
    if allocation:
        # Pura mapping sequence clean karein (Employee data remove karein agar corporate rule h)
        db.query(models.Employee).filter(models.Employee.id == allocation.employee_id).delete()
        db.delete(allocation)
    
    # Seat status wapas 'vacant' set karein
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat record not found")
        
    seat.status = "vacant"
    db.commit()
    
    return {"status": "success", "message": "Seat successfully released and marked as vacant"}