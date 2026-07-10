import random
from faker import Faker
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models

# Initialize Faker
fake = Faker()

def seed_database():
    print("🚀 Starting database seeding...")
    db: Session = SessionLocal()

    # 1. Clear out existing old data safely (Truncate/Delete)
    print("🧹 Cleaning old data...")
    db.query(models.SeatAllocation).delete()
    db.query(models.Seat).delete()
    db.query(models.Floor).delete()
    db.query(models.Project).delete()
    db.query(models.Employee).delete()
    db.commit()

    # 2. Generate Corporate Infrastructure (Floors & Seats)
    print("🏢 Creating building infrastructure (5 Floors, ~1,100 seats per floor)...")
    blocks = ["Block A", "Block B"]
    all_seats = []
    
    for floor_num in range(1, 6):  # 5 Floors
        block = random.choice(blocks)
        db_floor = models.Floor(floor_number=floor_num, block_name=block)
        db.add(db_floor)
        db.flush()  # Flush generates the floor UUID immediately for foreign keys

        # Create 1,100 desks per floor to accommodate ~5,500 total structural capacity
        for seat_num in range(1, 1101):
            seat_code = f"F{floor_num}-{block[6]}-{seat_num:04d}"  # e.g., F1-A-0001
            db_seat = models.Seat(
                seat_number=seat_code,
                floor_id=db_floor.id,
                status="vacant"
            )
            all_seats.append(db_seat)
            
    db.bulk_save_objects(all_seats)
    db.commit()

    # 3. Generate Employees (~5,000 records)
    print("👥 Generating 5,000 corporate employee profiles...")
    roles = ["employee", "employee", "employee", "pm", "hr", "admin"]  # Weighted probability
    all_employees = []
    used_emails = set()

    for _ in range(5000):
        name = fake.name()
        # Ensure email uniqueness
        email = f"{name.lower().replace(' ', '.')}@enterprise.com"
        if email in used_emails:
            email = f"{name.lower().replace(' ', '.')}{random.randint(1,99)}@enterprise.com"
        used_emails.add(email)

        db_employee = models.Employee(
            name=name,
            email=email,
            role=random.choice(roles),
            joining_date=fake.date_time_between(start_date="-2y", end_date="now")
        )
        all_employees.append(db_employee)

    db.bulk_save_objects(all_employees)
    db.commit()

    # 4. Generate Core Projects & Assign Managers
    print("📂 Constructing 50 active client projects...")
    pms = db.query(models.Employee).filter(models.Employee.role == "pm").all()
    all_projects = []
    
    for i in range(1, 51):
        manager = random.choice(pms) if pms else None
        db_project = models.Project(
            name=f"Project Alpha-{i:02d}" if i % 2 == 0 else f"Project Orion-{i:02d}",
            manager_id=manager.id if manager else None
        )
        all_projects.append(db_project)

    db.bulk_save_objects(all_projects)
    db.commit()

    # 5. Distribute Base Seat Allocations (~70% Occupancy Rate)
    print("🪑 Simulating 70% live seating occupancy...")
    employees = db.query(models.Employee).all()
    seats = db.query(models.Seat).all()
    projects = db.query(models.Project).all()

    random.shuffle(employees)
    random.shuffle(seats)

    # Allocate seats to roughly 70% of employees to leave room for analytics and new joiners
    allocations_count = int(len(employees) * 0.70)
    all_allocations = []

    for i in range(allocations_count):
        emp = employees[i]
        seat = seats[i]
        proj = random.choice(projects)

        # Update seat status memory reference
        seat.status = "occupied"
        
        db_alloc = models.SeatAllocation(
            employee_id=emp.id,
            seat_id=seat.id,
            project_id=proj.id
        )
        all_allocations.append(db_alloc)

    # Bulk update seat statuses
    db.commit()
    # Bulk save layout assignments
    db.bulk_save_objects(all_allocations)
    db.commit()

    print("🎉 Success! 5,000 Employees, 5,500 Seats, and Projects fully seeded.")
    db.close()

if __name__ == "__main__":
    seed_database()