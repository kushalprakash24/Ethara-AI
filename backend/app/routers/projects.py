from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/projects", tags=["Project Mapping"])

@router.get("/summary")
def get_project_mapping_summary(db: Session = Depends(get_db)):
    """
    Returns a high-level list of all projects along with their current headcounts
    and allocated desk counts.
    """
    # Aggregate allocations per project
    stats = db.query(
        models.Project.id.label("project_id"),
        models.Project.name.label("project_name"),
        func.count(models.SeatAllocation.id).label("allocated_headcount")
    ).outerjoin(models.SeatAllocation, models.Project.id == models.SeatAllocation.project_id)\
     .group_by(models.Project.id).all()

    return [dict(row._mapping) for row in stats]


@router.post("/bulk-map", status_code=status.HTTP_200_OK)
def bulk_map_employees_to_project(
    project_id: UUID, 
    employee_ids: List[UUID], 
    db: Session = Depends(get_db)
):
    """
    Enterprise utility: Maps a bulk batch of employees to a project at once.
    If they already have a seat allocation, it updates their project mapping safely.
    """
    # 1. Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found.")

    # 2. Update all active seat allocations matching these employee IDs
    updated_count = db.query(models.SeatAllocation)\
        .filter(models.SeatAllocation.employee_id.in_(employee_ids))\
        .update({"project_id": project_id}, synchronize_session=False)
        
    db.commit()
    
    return {
        "status": "success",
        "message": f"Successfully updated project mapping for {updated_count} employees to '{project.name}'."
    }