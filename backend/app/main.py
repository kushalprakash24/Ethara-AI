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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.7:3000"  # 👈 Jo aapka local network IP terminal me dikh rha tha, wo bhi add kar diya h
    ],
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