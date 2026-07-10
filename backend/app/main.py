from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from .database import engine, Base
from .routers import seats, dashboard, ai_assistant, projects

# Database tables create karne ke liye
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Seat Sync Enterprise Engine",
    version="1.0.0"
)

# 🌐 CORS Middleware - Frontend (React/Next.js) ko backend se connect karne ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active Routers
app.include_router(seats.router)
app.include_router(dashboard.router)  
app.include_router(ai_assistant.router)
app.include_router(projects.router)

@app.get("/")
def health_check():
    return {"status": "healthy"}

from sqlalchemy.orm import Session
from fastapi import Depends
from .database import SessionLocal  # Jo bhi aapka session creator ho
# Apne Faker waale script ya models ko import karein

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
       db.close()

@app.get("/seed-data")
def seed_database(db: Session = Depends(get_db)):
    # 💡 Yahan apna wahi Faker waala logic likhein jo aapne data generate karne ke liye likha tha
    # Example:
    # for _ in range(10):
    #     user = User(name=fake.name(), email=fake.email())
    #     db.add(user)
    # db.commit()
    return {"message": "Database seeded successfully with Faker data!"}