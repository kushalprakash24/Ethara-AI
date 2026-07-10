
# Ethara-AI: System Troubleshooting & Debugging Logs

A diagnostic handbook containing documented error signatures, infrastructure performance bottlenecks, and active runtime mitigation strategies for the Ethara-AI software stack.

---

## 🚨 Frequently Encountered Issues & Structural Fixes

### 1. Cross-Origin Resource Sharing (CORS) Exceptions
*   **Symptom:** Client browser console logs block fetch operations with a `No 'Access-Control-Allow-Origin' header` error string.
*   **Root Cause:** FastAPI backend application instances are not actively configured to intercept requests hailing from your specific frontend IP/domain address parameters.
*   **Mitigation Strategy:** Check `main.py` configurations. Ensure the `CORSMiddleware` setup explicitly accepts the target UI routing block origin:
    ```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "[http://127.0.0.1:3000](http://192.168.1.7:3000)"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

### 2. Network Port Bind Collision (`Address already in use`)
*   **Symptom:** Launching the FastAPI server throws a `[Errno 98] Address already in use` runtime exception.
*   **Root Cause:** A prior isolated instance or rogue thread is actively locking down port `8000`.
*   **Mitigation Strategy:** Find and kill the stale process using network diagnostics tools:
    ```bash
    # Identify the system task ID active on port 8000
    lsof -i :8000
    
    # Forcefully release the socket footprint using the process ID (PID)
    kill -9 <PID_NUMBER>
    ```

### 3. Strict Mode Type Inferences (TypeScript Compiler Flags)
*   **Symptom:** Next.js deployment builds fail out with error parameter diagnostics such as `Parameter 'X' implicitly has an 'any' type. ts(7006)`.
*   **Root Cause:** Strict TypeScript configuration sets enforce explicit signature assignments across all variable parameters.
*   **Mitigation Strategy:** Do not use implicit assignments. Explicitly pass type boundaries on parameter signatures:
    ```tsx
    const fetchFloorPlan = async (floorNum: number) => { ... }
    const handleOnboardSubmit = async (e: React.FormEvent) => { ... }
    ```

### 4. Database Deadlocks or Model Mapping Failures
*   **Symptom:** API endpoints hang or yield `500 Internal Server Errors` with SQLAlchemy trace warnings.
*   **Root Cause:** Uncommitted database sessions or mismatched columns between SQLAlchemy database model mappings and actual PostgreSQL table structures.
*   **Mitigation Strategy:** Always guarantee explicit database engine commits (`db.commit()`) or close active transactional cursor parameters using the context manager lifespan routine (`db.close()`).