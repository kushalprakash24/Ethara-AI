# Ethara-AI: Production Deployment Architecture Notes

This document provides blueprints and structural guidelines for deploying the Ethara-AI ecosystem onto cloud servers or live enterprise infrastructures.

---

## 🌐 Application Architecture Matrix

*   **Frontend (Next.js/React):** Deployed via Vercel / Netlify (Static/SSR Build Pipeline).
*   **Backend (FastAPI):** Deployed via Docker / AWS EC2 / DigitalOcean (Uvicorn ASGI Process Manager).
*   **Database (PostgreSQL):** Hosted via Managed Cloud Instances (AWS RDS / Supabase / Neon PostgreSQL).

---

## 🛠️ Step-by-Step Deployment Pipeline

### Phase 1: Database Provisioning
1. Spin up a secure Managed PostgreSQL instance.
2. Run the internal system schemas or initial migration scripts.
3. Execute the database seeding routine (`seed_database`) once to initialize asset floor configurations (Floor 1-5 maps).

### Phase 2: Production Backend Server Setup
1. Clone the master repository branch onto your target linux/unix virtual private instance.
2. Configure system environment production files (`.env`):
   ```env
   DATABASE_URL=postgresql://user:secure_password@host:port/database_name
   ENV_MODE=production
   CORS_ORIGINS=["["http://localhost:3000", "[http://127.0.0.1:3000](http://192.168.1.7:3000)"]]

Set up Gunicorn wrapping multiple asynchronous Uvicorn workers for process monitoring: 

gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

<!-- Frontend Client Infrastructure Deployment:  
NEXT_PUBLIC_API_URL=[https://myname.com](https://myname.com)  -->

Build the optimal production payload distribution directory:

npm run build