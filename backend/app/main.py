from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from sqladmin import Admin, ModelView  

from .database import engine, Base
from .routers import seats, dashboard, ai_assistant, projects

# 💡 Aapke actual models ko sahi se import kiya hai
from app.models import Employee, Project, Floor, Seat, SeatAllocation

# Database tables create karne ke liye
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Seat Sync Enterprise Engine",
    version="1.0.0"
)

# 🌐 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛠️ SQLAdmin Setup
admin = Admin(app, engine, title="Seat Sync Admin Panel")

# 📊 1. Employee Admin View
class EmployeeAdmin(ModelView, model=Employee):
    column_list = [Employee.id, Employee.name, Employee.email, Employee.role, Employee.joining_date]
    column_searchable_list = [Employee.name, Employee.email]
    form_columns = [Employee.name, Employee.email, Employee.role]

# 📊 2. Project Admin View
class ProjectAdmin(ModelView, model=Project):
    column_list = [Project.id, Project.name, Project.manager_id]
    column_searchable_list = [Project.name]
    form_columns = [Project.name, Project.manager_id]

# 📊 3. Floor Admin View
class FloorAdmin(ModelView, model=Floor):
    column_list = [Floor.id, Floor.floor_number, Floor.block_name]
    form_columns = [Floor.floor_number, Floor.block_name]

# 📊 4. Seat Admin View
class SeatAdmin(ModelView, model=Seat):
    column_list = [Seat.id, Seat.seat_number, Seat.status, Seat.floor_id]
    column_searchable_list = [Seat.seat_number]
    form_columns = [Seat.seat_number, Seat.status, Seat.floor_id]

# 📊 5. Seat Allocation Admin View
class SeatAllocationAdmin(ModelView, model=SeatAllocation):
    column_list = [SeatAllocation.id, SeatAllocation.employee_id, SeatAllocation.seat_id, SeatAllocation.project_id, SeatAllocation.allocated_at]
    form_columns = [SeatAllocation.employee_id, SeatAllocation.seat_id, SeatAllocation.project_id]

# ➕ Admin Panel me saare Views register kar rahe hain
admin.add_view(EmployeeAdmin)
admin.add_view(ProjectAdmin)
admin.add_view(FloorAdmin)
admin.add_view(SeatAdmin)
admin.add_view(SeatAllocationAdmin)

# Active Routers
app.include_router(seats.router)
app.include_router(dashboard.router)  
app.include_router(ai_assistant.router)
app.include_router(projects.router)

@app.get("/")
def health_check():
    return {"status": "healthy"}

from app.database import SessionLocal
# Agar aapki seed file me koi main function hai to use import karein, 
# ya fir direct seed.py wale logic ko yahan call kar sakte hain.
# Agar seed.py direct run hoti hai, to hum use terminal command ki tarah backend se execute karwa dete hain:
import subprocess

@app.get("/run-my-seed-data-123")
def run_seed_script():
    try:
        # Ye command wahi kaam karegi jo hum shell me karne wale the
        result = subprocess.run(["python", "seed.py"], capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}