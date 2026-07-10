# Ethara-AI: Relational Database Schema Blueprints

This document details the PostgreSQL relational database architecture designed for the Ethara-AI Enterprise Seating Management Core. The schema manages relational bounds between personnel entries, enterprise assets (desks/seats), and active project codes.

---

## 🗺️ Entity-Relationship Topology (Data Dictionary)


┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│    PROJECTS      │          │      SEATS       │          │    EMPLOYEES     │
├──────────────────┤          ├──────────────────┤          ├──────────────────┤
│ id (PK) [UUID]   │◄─────────┤ project_id (FK)  │         ┌┤ id (PK) [UUID]   │
│ name             │          │ employee_id (FK) ├─────────┘│ name             │
│ department       │          │ seat_code (UK)   │          │ email (UK)       │
└──────────────────┘          │ status           │          │ role             │
└──────────────────┘          └──────────────────┘


---

## 📑 Core Tables Definition

### 1. `projects` Table
Tracks enterprise client codes, internal projects, and cost-center buckets.
*   **Primary Key (`id`):** Unique System Identity via cryptographic `UUIDv4`.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique entity key. |
| `name` | `VARCHAR(100)` | `NOT NULL` | Project or team nomenclature. |
| `department` | `VARCHAR(50)` | `NULLABLE` | Operations/Engineering/HR domain classification. |

### 2. `employees` Table
Houses core personnel profiles available for workspace routing.
*   **Unique Index (`email`):** Double allocations or duplicate profile injections are barred system-wide via an explicit structural unique constraint layer.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique staff key. |
| `name` | `VARCHAR(100)` | `NOT NULL` | Employee full name profile. |
| `email` | `VARCHAR(100)` | `UNIQUE`, `NOT NULL` | System identity login/communication pointer. |
| `role` | `VARCHAR(50)` | `DEFAULT 'employee'` | Operations ranking parameter. |

### 3. `seats` Table (The Core Matrix Grid)
Maintains the floor grid layout configuration tracking individual desk nodes. 
*   **Foreign Keys Configuration:** Relational mapping triggers standard `ON DELETE SET NULL` constraints. If a project expires or an employee departs the system, target coordinates flush state variables instantly back to empty metrics (`vacant`) without mutating asset rows.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing relational integer proxy. |
| `seat_code` | `VARCHAR(20)` | `UNIQUE`, `NOT NULL` | Floor-plan coordinates (e.g., `FL1-D04`, `FL3-D59`). |
| `status` | `VARCHAR(20)` | `DEFAULT 'vacant'` | Functional asset current status (`vacant`, `occupied`). |
| `employee_id` | `UUID` | `FOREIGN KEY REFERENCES employees(id)` | Current desk occupant bind point. |
| `project_id` | `UUID` | `FOREIGN KEY REFERENCES projects(id)` | Team buffer reservation cluster mapping. |

---

## 🛠️ Raw SQL Generation Query (PostgreSQL Dialect)

```sql
-- Enable cryptographic sequence extensions for automated UUID handling
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Initialize Project Records Store
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50)
);

-- Initialize Employee Profiles Store
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'employee'
);

-- Initialize Active Seating Layout Grid Cache
CREATE TABLE seats (
    id SERIAL PRIMARY KEY,
    seat_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'vacant' CHECK (status IN ('vacant', 'occupied')),
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL
);

-- Create Fast Telemetry Optimization Indices for Real-Time Search Queries
CREATE INDEX idx_seats_status ON seats(status);
CREATE INDEX idx_seats_code ON seats(seat_code);
CREATE INDEX idx_employees_email ON employees(email);