import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .dashboard import search_directory, get_utilization_metrics

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.get("/ask")
def ask_assistant(q: str, db: Session = Depends(get_db)):
    """
    Natural Language Interface turning plain English into SQL/Dashboard parameters.
    """
    query_clean = q.lower().strip()

    # Pattern 1: "vacant seats on floor X" or "empty desks on floor X"
    floor_match = re.search(r'(?:vacant|empty|available).*?floor\s+(\d+)', query_clean)
    if not floor_match:
        floor_match = re.search(r'floor\s+(\d+).*?(?:vacant|empty|available)', query_clean)

    if floor_match:
        floor_num = int(floor_match.group(1))
        return {
            "intent": "find_vacant_seats_by_floor",
            "interpreted_query": f"Searching for all vacant seats located on Floor {floor_num}",
            "action_required": "redirect_to_map",
            "parameters": {"floor": floor_num, "status": "vacant"}
        }

# Pattern 2: "where does [Name] sit" or "find [Name]"
    find_match = re.search(r'(?:where does|find|who is|locate)\s+([a-zA-Z\s\.\d]+)', query_clean)
    if find_match:
        person_name = find_match.group(1).replace("sit", "").strip()
        
        # 💡 FIX: Explicitly pass primitive integers for limit and offset alongside the Nones
        search_res = search_directory(
            q=person_name, 
            project_id=None, 
            floor_id=None, 
            role=None,
            limit=10,      # 👈 Explicit int override
            offset=0,      # 👈 Explicit int override
            db=db
        )
        return {
            "intent": "locate_employee",
            "interpreted_query": f"Searching registry for employee matching: '{person_name}'",
            "data": search_res["results"]
        }

    # Pattern 3: "utilization metrics" or "system status"
    if any(keyword in query_clean for keyword in ["metrics", "status", "occupancy", "utilization", "report"]):
        metrics_res = get_utilization_metrics(db=db)
        return {
            "intent": "system_metrics",
            "interpreted_query": "Compiling global occupancy analytics summary.",
            "data": metrics_res["summary"]
        }

    return {
        "intent": "unknown",
        "interpreted_query": q,
        "message": "I didn't quite catch that. Try asking: 'Where does John sit?', 'Vacant seats on floor 2', or 'System utilization status'."
    }