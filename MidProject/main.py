"""
main.py
=======
Entry point for the Appointments Management System.

This file does exactly three things:
  1. Defines the Business configuration (edit here to reuse for any business).
  2. Initializes the database (creates tables from schema.sql if they don't exist).
  3. Launches the main menu (all further interaction is handled by ui.py).

To reuse this system for a different business, simply update the Business(...)
constructor call below — no other file needs to change.
"""

from Business import Business
from db import init_db
from features.appointments import auto_complete_past_appointments
from ui import menu_main

import sys

# Force UTF-8 output encoding for standard streams
sys.stdout.reconfigure(encoding='utf-8')


# ─────────────────────────────────────────────────────────────────────────────
# Business Configuration — edit these values to customize for any business
# ─────────────────────────────────────────────────────────────────────────────

business = Business(
    name="מאלף כלבים",
    services=["טיול", "אילוף", "אימונים"],
    working_hours={"start": "09:00", "end": "18:00"},
    owner="רוני שוורצמן"
)


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Initialize the SQLite database (creates tables if they don't exist yet).
    # The DB file (appointments.db) is created automatically on first run.
    init_db()

    # Auto-complete any past appointments that are still marked Pending.
    # Cancelled appointments are never touched.
    auto_complete_past_appointments()

    # Hand off to the UI layer — all menus and flows live in ui.py.
    menu_main(business)
