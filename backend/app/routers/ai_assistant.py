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

    if any(k in query_clean for k in ["available", "vacant", "empty", "free", "kitni seat", "khali"]):
        # Check if user specified a floor number
        floor_match = re.search(r'floor\s+(\d+)', query_clean)
        
        if floor_match:
            floor_num = int(floor_match.group(1))
            vacant_count = db.query(Seat).join(Floor).filter(Floor.floor_number == floor_num, Seat.status == "vacant").count()
            return {
                "intent": "vacant_count_floor",
                "interpreted_query": f"Counting available seats on Floor {floor_num}",
                "message": f"There are currently **{vacant_count} vacant seats** available on **Floor {floor_num}**. 🗺️",
                "action_required": "redirect_to_map",
                "parameters": {"floor": floor_num, "status": "vacant"}
            }
        else:
            total_vacant = db.query(Seat).filter(Seat.status == "vacant").count()
            return {
                "intent": "vacant_count_total",
                "interpreted_query": "Counting overall workplace availability",
                "message": f"Across the entire organization registry, there are currently **{total_vacant} unallocated/available seats** ready for allocation."
            }

    if "project" in query_clean and any(k in query_clean for k in ["how many", "list", "kitne", "members", "breakdown", "who"]):
        # Extract specific project name if present, e.g., "project alpha"
        project_match = re.search(r'(?:project)\s+([a-zA-Z0-9\s_-]+)', query_clean)
        
        if project_match:
            proj_name = project_match.group(1).strip()
            project = db.query(Project).filter(Project.name.ilike(f"%{proj_name}%")).first()
            if project:
                allocations = db.query(SeatAllocation).filter(SeatAllocation.project_id == project.id).all()
                emp_list = [alloc.employee.name for alloc in allocations if alloc.employee]
                count = len(emp_list)
                names_str = "\n   • " + "\n   • ".join(emp_list) if emp_list else "No active employees allocated."
                return {
                    "intent": "project_employees_specific",
                    "interpreted_query": f"Fetching team metrics for project: {project.name}",
                    "message": f"Project **{project.name}** has **{count} employees** assigned to it.\n\n**Allocated Members:**{names_str}"
                }
        
        # General Breakdown across all projects
        proj_counts = db.query(Project.name, func.count(SeatAllocation.id)).\
            outerjoin(SeatAllocation, Project.id == SeatAllocation.project_id).\
            group_by(Project.name).all()
        
        msg = "📊 **Active Project Allocations Breakdown:**\n"
        for p_name, p_count in proj_counts:
            msg += f"• Project **{p_name}**: {p_count} assigned employees\n"
            
        return {
            "intent": "project_employees_all",
            "interpreted_query": "Compiling global project workforce directory metrics",
            "message": msg
        }


    find_match = re.search(r'(?:where does|find|who is|locate|allocated|allocation for|joiner)\s+([a-zA-Z\s\.\d]+)', query_clean)
    if find_match:
        person_name = find_match.group(1).replace("sit", "").replace("status", "").replace("seat", "").replace("new joiner", "").strip()
        search_res = search_directory(q=person_name, project_id=None, floor_id=None, role=None, limit=5, offset=0, db=db)
        results = search_res.get("results", [])
        
        if not results:
            return {
                "intent": "locate_employee",
                "interpreted_query": f"Querying master registry for: '{person_name}'",
                "message": f"Could not find any employee matching **'{person_name}'** in the database registry."
            }
        
        emp = results[0]
        location = emp.get("location", "Remote")
        
        # Check if they have a real seat vs being a new joiner still unallocated
        if "floor" in location.lower():
            msg = f"🔍 **Registry Found:** Employee **{emp['name']}** is active and currently seated at **{location}**."
        else:
            msg = f"⚠️ **Unallocated Record:** Employee **{emp['name']}** is registered in the database but **has not been allocated a workspace seat yet** (Status: Remote / Pending Onboarding Allocation)."

        return {
            "intent": "locate_employee",
            "interpreted_query": f"Locating desk allocation for: '{emp['name']}'",
            "message": msg,
            "data": results
        }


    if any(keyword in query_clean for keyword in ["metrics", "status", "occupancy", "utilization", "report", "stats"]):
        metrics_res = get_utilization_metrics(db=db)
        summary = metrics_res.get("summary", {})
        
        return {
            "intent": "system_metrics",
            "interpreted_query": "Compiling unified workplace occupancy analytics.",
            "message": f"📊 **System Capacity & Seat Utilization Metrics Report:**\n\n"
                       f"• **Total Workspace Inventory:** {summary.get('total_desks')} Desks\n"
                       f"• **Active Occupancy:** {summary.get('occupied_seats')} Seats Assigned\n"
                       f"• **Immediate Availability:** {summary.get('vacant_seats')} Seats Open\n"
                       f"• **Global Infrastructure Utilization Rate:** **{summary.get('utilization_rate')}%**",
            "data": summary
        }


    if any(k in query_clean for k in ["reset", "clear", "show all", "everyone"]):
        return {
            "intent": "reset_filter",
            "interpreted_query": "Resetting table search filters",
            "message": "Cleared custom AI workspace filters. Displaying global master registry.",
            "trigger_reset": True
        }

    # Default Fallback UI Guide
    return {
        "intent": "unknown",
        "interpreted_query": q,
        "message": "🤖 **Hi! I am your AI Workspace Assistant. Here is what I can query directly via Natural Language:**\n\n"
                   "• *'How many seats are available?'* or *'Available seats on floor 2'* 🪑\n"
                   "• *'Which project has how many employees?'* or *'List members on project Alpha'* 👥\n"
                   "• *'Where does Andre Moore sit?'* or check allocation status *'Is new joiner John allocated?'* 📍\n"
                   "• *'Show global seat utilization metrics summary.'* 📊"
    }