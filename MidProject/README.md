# Appointments Management System
**Mid-course Python Project**

A general-purpose CLI appointment management system written in Python,
storing all data in a persistent SQLite database. The system is designed to be
reusable for any type of business — simply update the configuration in `main.py`.

---

## How to Install & Run

### Requirements
- Python 3.8 or higher (no external packages required — only Python standard library)
- Standard library used: `sqlite3`, `datetime`, `os`

### Running the Project
1. Extract the ZIP archive and navigate to the project folder:
   ```
   cd MidProject
   ```
2. Run the entry point:
   ```
   python main.py
   ```
   On some systems, use `python3` instead of `python`.

3. On the **first run**, the file `appointments.db` is created automatically.  
   You do not need to create it manually.

4. Navigate using the numbered menus. Enter `0` at any menu to go back.

> **Note:** `appointments.db` is **not** included in the submitted ZIP (as required by the project manual). It is auto-generated on first run.

---

## File Structure

| File | Responsibility |
|---|---|
| `main.py` | Entry point — defines Business config, initializes DB, launches UI |
| `Business.py` | `Business` class — holds name, services, working hours |
| `db.py` | SQLite connection with FK enforcement + `init_db()` from `schema.sql` |
| `schema.sql` | All table definitions (customers, appointments, invoices, leads) |
| `ui.py` | All user interaction — menus, input helpers, ANSI colors, tables |
| `features/__init__.py` | Makes `features/` a Python package |
| `features/appointments.py` | Appointment CRUD + conflict detection |
| `features/customers.py` | Customer CRUD + history retrieval |
| `features/invoice.py` | Invoice creation + listing |
| `features/leads.py` | Lead CRUD + lead-to-customer conversion |

---

## What Was Implemented

### Mandatory Technical Requirements
- **Python + SQLite**: all data is saved in `appointments.db` — no text files, no in-memory-only lists.
- **Schema in a separate file**: `schema.sql` defines all tables with primary keys and foreign keys.
- **Modular code structure**: 10 files each with a single, clear responsibility (Separation of Concerns).
- **Input validation**: empty fields rejected, date/time format enforced via `datetime.strptime`, invalid statuses rejected, times outside working hours rejected.
- **README**: this file.

### Mandatory Functional Requirements
| Feature | Where implemented |
|---|---|
| Add new appointment (name, service, date, time) | `features/appointments.py` → `add_appointment()` |
| View all appointments | `features/appointments.py` → `get_all_appointments()` |
| Update appointment status (Pending / Completed / Cancelled) | `features/appointments.py` → `update_status()` |
| Delete appointment | `features/appointments.py` → `delete_appointment()` |
| Basic conflict detection (warn on same date+time slot) | `features/appointments.py` → `check_conflict()` |

### Bonus 1: Customer Management & Invoices (up to +10%)
- Separate `customers` table (name, phone, email, address).
- Add, view, delete customers via `features/customers.py`.
- Foreign key linking appointments to customers (optional, so standalone appointments still work).
- Auto-generated invoice numbers (`INV-0001`, `INV-0002`, …) with unique constraint — `features/invoice.py`.
- View full customer history: all their appointments and invoices — `customers.get_customer_history()`.

### Bonus 2: Lead Management (up to +5%)
- Separate `leads` table (name, phone, source, status, notes) — `features/leads.py`.
- Add leads, update status (New / In Progress / Converted / Rejected).
- Convert a lead to a customer with one action: creates a customer record from lead data,
  and automatically updates the lead's status to "Converted".

---

## Design Decisions

### Business Class
The `Business` class in `Business.py` holds all business-specific configuration:
name, service list, and working hours. This makes the system fully reusable —
changing the business only requires editing the three lines in `main.py`
where `Business(...)` is constructed.

### Separation of Concerns
`ui.py` is the **only** file that calls `input()` and `print()`.  
All feature modules contain pure logic and SQL — zero UI coupling.  
This design is intentional and maps directly to the grading criteria for code quality.

### Foreign Keys
SQLite foreign key enforcement is off by default. `db.get_connection()` enables it
with `PRAGMA foreign_keys = ON` on every connection, ensuring:
- `ON DELETE CASCADE` on invoices (deleting a customer removes their invoices).
- `ON DELETE SET NULL` on appointments (deleting a customer unlinks but keeps appointments).

### Date & Time Format
`DD/MM/YYYY` and `HH:MM` formats were chosen for clarity.  
Validation uses `datetime.strptime`, which rejects invalid dates like `31/02/2026`.

### Invoice Numbering
Invoice numbers are auto-generated sequentially (`INV-0001`, `INV-0002`, …)
by querying the current maximum in the table. No user input required, no duplicates possible.
