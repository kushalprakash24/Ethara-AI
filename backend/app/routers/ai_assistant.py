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

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query_clean)
    find_match = re.search(r'(?:where is employee|where does|find|who is|locate|allocated|allocation for|where is my seat)\s+([a-zA-Z\s\.\d@\-_]+)', query_clean)
    
    if email_match or find_match:
        # 1. Determine search filter based on input type (Email vs Name)
        if email_match:
            user_email = email_match.group(0).strip()
            db_emp = db.query(Employee).filter(Employee.email.ilike(user_email)).first()
        else:
            person_name = find_match.group(1).replace("sit", "").replace("seated", "").replace("status", "").replace("seat", "").replace("my email is", "").strip()
            db_emp = db.query(Employee).filter(Employee.name.ilike(f"%{person_name}%")).first()
        
        if not db_emp:
            return {
                "intent": "locate_employee",
                "interpreted_query": "Querying master identity logs",
                "message": '{\n  "error": "Could not find any employee matching the criteria in the registry database."\n}'
            }
        
        # 2. Extract allocation records if active
        if db_emp.allocation and db_emp.allocation.seat:
            alloc = db_emp.allocation
            seat = alloc.seat
            floor = seat.floor
            project_name = alloc.project.name if alloc.project else "No Active Project"
            
            # Extract Bay from seat number structure (e.g., 'B4-23' -> '4')
            seat_num = seat.seat_number
            bay_match = re.search(r'[a-zA-Z](\d+)-', seat_num)
            bay_name = bay_match.group(1) if bay_match else "4"
            
            # 3. 🔥 Formulate customized response style based on user's query prompt
            if email_match:
                # Returns exact JSON structure formatting requested for email checks
                msg = f'{{\n  "answer": "You are allocated Floor {floor.floor_number}, Zone {floor.block_name}, Bay {bay_name}, Seat {seat_num}. Your project is {project_name}."\n}}'
            else:
                # Returns standard corporate string structure for name checks
                msg = f"**{db_emp.name}** is seated on **Floor {floor.floor_number}**, **Zone {floor.block_name}**, **Bay {bay_name}**, **Seat {seat_num}**. He is assigned to **Project {project_name}**."
            
            return {
                "intent": "locate_employee",
                "interpreted_query": f"Locating workspace assets for: {db_emp.name}",
                "message": msg,
                "action_required": "redirect_to_map",
                "parameters": {"floor": floor.floor_number, "seat_id": str(seat.id)}
            }
        else:
            # Unallocated/Remote state handler
            project_name = db_emp.allocation.project.name if (db_emp.allocation and db_emp.allocation.project) else "None"
            if email_match:
                msg = f'{{\n  "answer": "You are active on Project {project_name}, but no physical seat has been allocated to you yet."\n}}'
            else:
                msg = f"**{db_emp.name}** is registered under **Project {project_name}** but currently has no physical seat allocation (Status: Remote)."
                
            return {
                "intent": "locate_employee",
                "interpreted_query": f"Locating workspace assets for: {db_emp.name}",
                "message": msg
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