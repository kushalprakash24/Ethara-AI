import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .dashboard import search_directory, get_utilization_metrics
from ..models import Employee, Seat, SeatAllocation, Project, Floor 

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.get("/ask")
def ask_assistant(q: str, db: Session = Depends(get_db)):
    query_clean = q.lower().strip()

    # =========================================================================
    # TASK 1: "kitni seat available/vacant hain" (Total or Floor-wise Available Counts)
    # =========================================================================
    if any(k in query_clean for k in ["how many available", "how many vacant", "how many empty", "kitni seat available", "available seats count"]):
        # Check if asking for a specific floor (e.g., "on floor 2")
        floor_match = re.search(r'floor\s+(\d+)', query_clean)
        
        if floor_match:
            floor_num = int(floor_match.group(1))
            vacant_count = db.query(Seat).join(Floor).filter(Floor.floor_number == floor_num, Seat.status == "vacant").count()
            return {
                "intent": "vacant_count_floor",
                "interpreted_query": f"Counting available seats on Floor {floor_num}",
                "message": f"Floor {floor_num} par abhi kul **{vacant_count} seats** available hain. 🗺️",
                "action_required": "redirect_to_map",
                "parameters": {"floor": floor_num, "status": "vacant"}
            }
        else:
            total_vacant = db.query(Seat).filter(Seat.status == "vacant").count()
            return {
                "intent": "vacant_count_total",
                "interpreted_query": "Counting total available seats across organization",
                "message": f"Pure office me abhi total **{total_vacant} seats** khali (available) hain."
            }

    # =========================================================================
    # TASK 2: "kis project pr kitne employee h" (Project-wise Employee List & Count)
    # =========================================================================
    if "project" in query_clean and any(k in query_clean for k in ["how many employee", "list", "kitne employee", "members"]):
        # Extract project name if specified, e.g., "project alpha"
        project_match = re.search(r'(?:project)\s+([a-zA-Z0-9\s_-]+)', query_clean)
        
        if project_match:
            proj_name = project_match.group(1).strip()
            project = db.query(Project).filter(Project.name.ilike(f"%{proj_name}%")).first()
            if project:
                allocations = db.query(SeatAllocation).filter(SeatAllocation.project_id == project.id).all()
                emp_list = [alloc.employee.name for alloc in allocations if alloc.employee]
                count = len(emp_list)
                names_str = ", ".join(emp_list) if emp_list else "None"
                return {
                    "intent": "project_employees_specific",
                    "interpreted_query": f"Fetching team for project: {project.name}",
                    "message": f"Project **{project.name}** par kul **{count} employees** assigned hain.\n\n**Team Members:** {names_str}"
                }
        
        # General query: Show list of all projects with their breakdown counts
        proj_counts = db.query(Project.name, func.count(SeatAllocation.id)).\
            outerjoin(SeatAllocation, Project.id == SeatAllocation.project_id).\
            group_by(Project.name).all()
        
        msg = "**Project Breakdown Counts:**\n"
        for p_name, p_count in proj_counts:
            msg += f"• Project *{p_name}*: **{p_count} employees**\n"
            
        return {
            "intent": "project_employees_all",
            "interpreted_query": "Compiling project workforce counts breakdown",
            "message": msg
        }

    # =========================================================================
    # TASK 3: Where an employee is seated & New Joiner allocation status
    # =========================================================================
    find_match = re.search(r'(?:where does|find|who is|locate|allocated|allocation for)\s+([a-zA-Z\s\.\d]+)', query_clean)
    if find_match:
        person_name = find_match.group(1).replace("sit", "").replace("status", "").strip()
        search_res = search_directory(q=person_name, project_id=None, floor_id=None, role=None, limit=5, offset=0, db=db)
        results = search_res.get("results", [])
        
        if not results:
            return {
                "intent": "locate_employee",
                "interpreted_query": f"Checking records for '{person_name}'",
                "message": f"Sorry, record registry me '{person_name}' naam ka koi employee nahi mila."
            }
        
        emp = results[0]
        location = emp.get("location", "Remote")
        
        if "floor" in location.lower():
            msg = f"**{emp['name']}** successfully allocated hain! Wo **{location}** par baithte hain."
        else:
            msg = f"**{emp['name']}** abhi system me registered hain par unhe koi seat allocate nahi hui hai (Status: Remote/Unallocated)."

        return {
            "intent": "locate_employee",
            "interpreted_query": f"Locating: '{emp['name']}'",
            "message": msg,
            "data": results
        }

    # =========================================================================
    # TASK 4: Seat utilization (Global Metrics Summary)
    # =========================================================================
    if any(keyword in query_clean for keyword in ["metrics", "status", "occupancy", "utilization", "report", "stats"]):
        metrics_res = get_utilization_metrics(db=db)
        summary = metrics_res.get("summary", {})
        
        return {
            "intent": "system_metrics",
            "interpreted_query": "Compiling global seat utilization summary.",
            "message": f"📊 **Seat Utilization Summary:**\n• Total Desks: **{summary.get('total_desks')}**\n• Occupied: **{summary.get('occupied_seats')}**\n• Available: **{summary.get('vacant_seats')}**\n• Current Utilization Rate: **{summary.get('utilization_rate')}%**",
            "data": summary
        }

    # Default Fallback Help Guide
    return {
        "intent": "unknown",
        "interpreted_query": q,
        "message": "🤖 **Hi! I can process all complex layout queries instantly. Try asking:**\n"
                   "1. *'Kitni seat available h?'* ya *'Available seats on floor 2'* 🪑\n"
                   "2. *'Kis project pr kitne employee h?'* ya *'List employees in project Alpha'* 👥\n"
                   "3. *'Where does Andre Moore sit?'* 📍\n"
                   "4. *'Show seat utilization stats'* 📊"
    }