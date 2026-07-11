import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .dashboard import search_directory, get_utilization_metrics
# Make sure to import your models properly based on your project structure
from ..models import Employee, Seat, SeatAllocation, Project, Floor 

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.get("/ask")
def ask_assistant(q: str, db: Session = Depends(get_db)):
    query_clean = q.lower().strip()

    # 1. TASK: Where an employee is seated & Whether a new joiner has been allocated a seat
    # Queries like: "where does John sit?", "find employee Sarah", "is new joiner Amit allocated a seat?"
    find_match = re.search(r'(?:where does|find|who is|locate|allocated a seat|allocation for)\s+([a-zA-Z\s\.\d]+)', query_clean)
    if find_match:
        person_name = find_match.group(1).replace("sit", "").replace("status", "").strip()
        
        search_res = search_directory(q=person_name, project_id=None, floor_id=None, role=None, limit=5, offset=0, db=db)
        results = search_res.get("results", [])
        
        if not results:
            return {
                "intent": "locate_employee",
                "interpreted_query": f"Checking seat allocation for '{person_name}'",
                "message": f"Sorry, no record found for '{person_name}'. Please check the spelling."
            }
        
        # Checking specific seat details from the registry search
        emp = results[0] # Take the best match
        location = emp.get("location", "Remote")
        
        if "floor" in location.lower():
            msg = f"{emp['name']} is currently seated at {location}."
        else:
            msg = f"{emp['name']} has not been allocated a physical seat yet (Status: Remote/Unallocated)."

        return {
            "intent": "locate_employee",
            "interpreted_query": f"Locating employee and seat assignment for: '{emp['name']}'",
            "message": msg,
            "data": results
        }

    # 2. TASK: Which project the employee is assigned to
    # Queries like: "which project is Rohan assigned to?", "what project is John working on?"
    project_emp_match = re.search(r'(?:which project|what project|project for)\s+([a-zA-Z\s\.\d]+)', query_clean)
    if project_emp_match:
        emp_name = project_emp_match.group(1).replace("assigned to", "").replace("working on", "").strip()
        
        # Database query to fetch employee along with project through allocation
        db_emp = db.query(Employee).filter(Employee.name.ilike(f"%{emp_name}%")).first()
        if db_emp and db_emp.allocation and db_emp.allocation.project:
            return {
                "intent": "employee_project",
                "interpreted_query": f"Finding project track for {db_emp.name}",
                "message": f"{db_emp.name} is assigned to the project: '**{db_emp.allocation.project.name}**'."
            }
        elif db_emp:
            return {
                "intent": "employee_project",
                "interpreted_query": f"Finding project track for {db_emp.name}",
                "message": f"{db_emp.name} is currently not assigned to any active project."
            }

    # 3. TASK: Which floor/zone/seat is available
    # Queries like: "vacant seats on floor 2", "which seats are available on floor 1?"
    floor_match = re.search(r'(?:vacant|empty|available|free).*?floor\s+(\d+)', query_clean)
    if not floor_match:
        floor_match = re.search(r'floor\s+(\d+).*?(?:vacant|empty|available|free)', query_clean)

    if floor_match:
        floor_num = int(floor_match.group(1))
        return {
            "intent": "find_vacant_seats_by_floor",
            "interpreted_query": f"Searching for available seats on Floor {floor_num}",
            "action_required": "redirect_to_map",
            "parameters": {"floor": floor_num, "status": "vacant"},
            "message": f"Redirecting you to the live layout map of **Floor {floor_num}** highlighting all available desks."
        }

    # 4. TASK: Seat utilization by project, floor, and team (Global analytics summary)
    # Queries like: "seat utilization", "occupancy report", "utilization by floor", "system status"
    if any(keyword in query_clean for keyword in ["metrics", "status", "occupancy", "utilization", "report", "stats"]):
        metrics_res = get_utilization_metrics(db=db)
        summary = metrics_res.get("summary", {})
        
        return {
            "intent": "system_metrics",
            "interpreted_query": "Compiling seat utilization metrics summary.",
            "message": f"📊 **Seat Utilization Report:** Total Desks: {summary.get('total_desks')}, Occupied: {summary.get('occupied_seats')}, Available: {summary.get('vacant_seats')}. Utilization Rate is **{summary.get('utilization_rate')}%**.",
            "data": summary
        }

    # 5. Default fallback for generic/unknown queries
    return {
        "intent": "unknown",
        "interpreted_query": q,
        "message": "🤖 I can assist you with all seat and project queries! Try asking:\n"
                   "• *'Where does Andre Moore sit?'*\n"
                   "• *'Which project is Steven Travis assigned to?'*\n"
                   "• *'Which seats are available on floor 2?'*\n"
                   "• *'Show me the seat utilization metrics.'*"
    }