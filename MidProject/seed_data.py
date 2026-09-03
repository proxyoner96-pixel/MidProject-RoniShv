"""
seed_data.py
============
Populates the database with realistic sample data for a dog-training business
("מאלף כלבים"). Run this ONCE after creating a fresh database.

Usage:
    python seed_data.py

WARNING: Running this on an existing database will ADD duplicate records.
         Delete appointments.db first if you want a clean start.
"""

import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from db import init_db, get_connection
from features import appointments, customers, invoice, leads
from features.appointments import update_status

init_db()

print("Seeding database with sample data...\n")

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMERS (10)
# ─────────────────────────────────────────────────────────────────────────────

customer_data = [
    # (name, phone, email, address, id_number)
    ("דני לוי",        "050-1234567", "danny@gmail.com",    "רחוב הרצל 12, תל אביב",        "200000001"),
    ("מיכל כהן",       "052-9876543", "michal@walla.co.il", "שדרות בן גוריון 5, חיפה",       "200000002"),
    ("יוסי ברוך",      "054-1112233", "yossi@gmail.com",    "רחוב ויצמן 8, ירושלים",         "200000003"),
    ("שרה גולדשטיין",  "053-4455667", "sara@gmail.com",     "אבן גבירול 22, תל אביב",        "200000004"),
    ("אמיר פרץ",       "058-8889900", "amir@hotmail.com",   "הנשיא 3, חדרה",                "200000005"),
    ("ליאור שפירא",    "050-6677889", "lior@gmail.com",     "דיזנגוף 55, תל אביב",           "200000006"),
    ("נועה אברהם",     "052-3344556", "noa@gmail.com",      "הגפן 10, פתח תקווה",            "200000007"),
    ("רוני אוחיון",    "054-7788990", "roni@walla.co.il",   "רמב\"ם 7, נתניה",               "200000008"),
    ("תמר לוינטל",     "053-2233445", "tamar@gmail.com",    "הבנים 14, ראשון לציון",         "200000009"),
    ("גיל מזרחי",      "058-5566778", "gil@gmail.com",      "כצנלסון 9, גבעתיים",            "200000010"),
    # Extra customer sharing a first name with #1 ("דני") — needed to test the
    # "ambiguous name → bot asks for clarification" scenario from the brief.
    ("דני כהן",        "050-1112222", "dani.cohen@gmail.com","העצמאות 20, רמת גן",           "200000011"),
]

cust_ids = []
for name, phone, email, addr, id_number in customer_data:
    cid = customers.add_customer(name, phone, email, addr, id_number)
    cust_ids.append(cid)
    print(f"  Customer added: {name} (ID {cid})")

print(f"\n  ✔ {len(cust_ids)} customers created.\n")

# ─────────────────────────────────────────────────────────────────────────────
# APPOINTMENTS (20) — mix of past/future and all three statuses
# ─────────────────────────────────────────────────────────────────────────────

appointment_data = [
    # (customer_index, service, date, time, status_override)
    # Past — auto-completed on startup, but we set explicitly here for clarity
    (0,  "אילוף",    "05/01/2026", "10:00", "Completed"),
    (1,  "טיול",     "12/01/2026", "09:00", "Completed"),
    (2,  "אימונים",  "20/01/2026", "11:30", "Completed"),
    (3,  "אילוף",    "03/02/2026", "14:00", "Completed"),
    (4,  "טיול",     "15/02/2026", "09:30", "Cancelled"),
    (5,  "אימונים",  "01/03/2026", "16:00", "Completed"),
    (6,  "אילוף",    "10/03/2026", "10:00", "Cancelled"),
    (7,  "טיול",     "22/03/2026", "08:30", "Completed"),
    (8,  "אימונים",  "05/04/2026", "15:00", "Completed"),
    (9,  "אילוף",    "18/04/2026", "11:00", "Completed"),
    (0,  "טיול",     "02/05/2026", "09:00", "Completed"),
    (1,  "אימונים",  "14/05/2026", "13:00", "Completed"),
    (2,  "אילוף",    "28/05/2026", "10:30", "Cancelled"),
    (3,  "טיול",     "10/06/2026", "09:00", "Completed"),
    # Future — will remain Pending
    (4,  "אילוף",    "15/08/2026", "10:00", None),
    (5,  "טיול",     "18/08/2026", "09:00", None),
    (6,  "אימונים",  "20/08/2026", "14:00", None),
    (7,  "אילוף",    "25/08/2026", "11:00", None),
    (8,  "טיול",     "01/09/2026", "09:30", None),
    (9,  "אימונים",  "10/09/2026", "16:00", None),
]

appt_ids = []
for cust_idx, service, date, time, status_override in appointment_data:
    aid = appointments.add_appointment(
        customer_name=customer_data[cust_idx][0],
        service_type=service,
        appointment_date=date,
        appointment_time=time,
        customer_id=cust_ids[cust_idx],
    )
    if status_override:
        update_status(aid, status_override)
    appt_ids.append(aid)
    status_label = status_override if status_override else "Pending"
    print(f"  Appointment added: {customer_data[cust_idx][0]:18} | {date} {time} | {status_label}")

print(f"\n  ✔ {len(appt_ids)} appointments created.\n")

# ─────────────────────────────────────────────────────────────────────────────
# INVOICES (12) — for past completed appointments
# ─────────────────────────────────────────────────────────────────────────────

invoice_data = [
    # (customer_index, amount)
    (0,  250.0),
    (1,  180.0),
    (2,  320.0),
    (3,  250.0),
    (5,  320.0),
    (7,  180.0),
    (8,  320.0),
    (9,  250.0),
    (0,  250.0),   # second invoice for same customer
    (1,  180.0),
    (3,  250.0),
    (6,  320.0),
]

for cust_idx, amount in invoice_data:
    result = invoice.create_invoice(cust_ids[cust_idx], amount)
    print(f"  Invoice {result['invoice_number']:8} → {customer_data[cust_idx][0]:18} | {amount:.0f} ILS")

print(f"\n  ✔ {len(invoice_data)} invoices created.\n")

# ─────────────────────────────────────────────────────────────────────────────
# LEADS (8) — mix of statuses
# ─────────────────────────────────────────────────────────────────────────────

lead_data = [
    ("אורן טל",        "050-1010101", "פייסבוק",    "New",         "מתעניין באילוף לכלב צעיר"),
    ("יעל עזולאי",     "052-2020202", "המלצה",       "In Progress", "התקשרה, ממתינה לפגישת היכרות"),
    ("עמוס ביטון",     "054-3030303", "אתר אינטרנט", "Converted",   "הפך ללקוח - ראשון שלה"),
    ("חן פרידמן",      "053-4040404", "אינסטגרם",    "New",         "ראה פרסומת, מתעניין בטיולים"),
    ("מורן כץ",        "058-5050505", "המלצה",       "Rejected",    "לא רלוונטי כרגע, כלב קשיש"),
    ("איתן שמש",       "050-6060606", "פייסבוק",     "In Progress", "שאל על מחירים, שלחנו הצעה"),
    ("דנה ויסמן",      "052-7070707", "גוגל",        "New",         "חיפוש אילוף לכלב אגרסיבי"),
    ("ניר קסלר",       "054-8080808", "המלצה",       "In Progress", "נפגשנו, מחכה להחלטה"),
]

for name, phone, source, status, notes in lead_data:
    lid = leads.add_lead(name, phone, source, notes)
    if status != "New":
        leads.update_lead_status(lid, status)
    print(f"  Lead added: {name:18} | {source:14} | {status}")

print(f"\n  ✔ {len(lead_data)} leads created.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

with get_connection() as conn:
    n_custs  = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    n_appts  = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    n_invs   = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    n_leads  = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    revenue  = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices").fetchone()[0]

print("=" * 50)
print("  DATABASE SUMMARY")
print("=" * 50)
print(f"  Customers:    {n_custs}")
print(f"  Appointments: {n_appts}")
print(f"  Invoices:     {n_invs}")
print(f"  Leads:        {n_leads}")
print(f"  Total Revenue: {revenue:.0f} ILS")
print("=" * 50)
print("\n  Seed complete! Run `python main.py` to start the app.\n")
