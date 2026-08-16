"""
features/appointments.py
=========================
Business logic and database operations for Appointment management.

This module contains ONLY logic and DB queries — no input() or print() calls.
All user interaction happens in ui.py.

Implements the mandatory core requirements:
  - add_appointment             : "הוספת תור חדש"         (required)
  - get_all_appointments        : "הצגת רשימת כל התורים"  (required)
  - update_status               : "עדכון סטטוס תור"         (required)
  - delete_appointment          : "מחיקת תור"              (required)
  - check_conflict              : "מניעת התנגשויות"         (advantage bonus)

Additional features:
  - auto_complete_past_appointments : mark past Pending appointments as Completed
  - get_todays_appointments         : return only today's appointments
  - search_appointments             : filter by status, date range, customer name
"""

from db import get_connection
from datetime import datetime

# Allowed appointment status values.
STATUS_OPTIONS = ["Pending", "Completed", "Cancelled"]


def auto_complete_past_appointments() -> int:
    """
    Automatically mark past appointments as 'Completed'.

    Any appointment whose date+time is earlier than the current moment
    and whose status is still 'Pending' is updated to 'Completed'.
    Appointments with status 'Cancelled' are never touched.

    Called once at startup from main.py, right after init_db().

    Returns:
        The number of appointments that were updated.
    """
    now = datetime.now()

    sql = "SELECT id, appointment_date, appointment_time FROM appointments WHERE status = 'Pending'"
    ids_to_complete = []

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        for row in rows:
            try:
                appt_dt = datetime.strptime(
                    f"{row['appointment_date']} {row['appointment_time']}",
                    "%d/%m/%Y %H:%M",
                )
                if appt_dt < now:
                    ids_to_complete.append(row["id"])
            except ValueError:
                # Skip rows with unexpected date/time format
                continue

        if ids_to_complete:
            placeholders = ",".join("?" * len(ids_to_complete))
            conn.execute(
                f"UPDATE appointments SET status = 'Completed' WHERE id IN ({placeholders})",
                ids_to_complete,
            )

    return len(ids_to_complete)


def add_appointment(
    customer_name: str,
    service_type: str,
    appointment_date: str,
    appointment_time: str,
    customer_id: int = None,
) -> int:
    """
    Insert a new appointment into the database.

    Args:
        customer_name:    Name of the customer (required, non-empty).
        service_type:     Type of service (required, non-empty).
        appointment_date: Date in DD/MM/YYYY format.
        appointment_time: Time in HH:MM format.
        customer_id:      Optional FK to the customers table.

    Returns:
        The integer ID of the newly created appointment.

    Raises:
        ValueError: If customer_name or service_type is empty.
    """
    if not customer_name.strip():
        raise ValueError("Customer name cannot be empty.")
    if not service_type.strip():
        raise ValueError("Service type cannot be empty.")

    sql = """
        INSERT INTO appointments
            (customer_id, customer_name, service_type, appointment_date, appointment_time, status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (customer_id, customer_name.strip(), service_type.strip(),
                                    appointment_date, appointment_time))
        return cursor.lastrowid


def get_all_appointments() -> list:
    """
    Retrieve all appointments from the database, ordered by date and time.

    Returns:
        A list of sqlite3.Row objects (accessible by column name).
    """
    sql = """
        SELECT id, customer_name, service_type, appointment_date, appointment_time, status
        FROM appointments
        ORDER BY appointment_date, appointment_time
    """
    with get_connection() as conn:
        return conn.execute(sql).fetchall()


def update_status(appointment_id: int, new_status: str) -> bool:
    """
    Update the status of an existing appointment.

    Args:
        appointment_id: The integer ID of the appointment to update.
        new_status:     The new status string. Must be one of STATUS_OPTIONS.

    Returns:
        True if the row was found and updated, False if no row matched the ID.

    Raises:
        ValueError: If new_status is not in STATUS_OPTIONS.
    """
    if new_status not in STATUS_OPTIONS:
        raise ValueError(
            f"Invalid status '{new_status}'. Choose from: {', '.join(STATUS_OPTIONS)}"
        )
    sql = "UPDATE appointments SET status = ? WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.execute(sql, (new_status, appointment_id))
        return cursor.rowcount > 0


def delete_appointment(appointment_id: int) -> bool:
    """
    Delete an appointment by its ID.

    Args:
        appointment_id: The integer ID of the appointment to delete.

    Returns:
        True if the row was found and deleted, False if no row matched.
    """
    sql = "DELETE FROM appointments WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.execute(sql, (appointment_id,))
        return cursor.rowcount > 0


def check_conflict(appointment_date: str, appointment_time: str) -> list:
    """
    Check whether an active (Pending) appointment already exists at the given
    date and time. Used to warn the user before adding a new appointment.

    Args:
        appointment_date: Date in DD/MM/YYYY format.
        appointment_time: Time in HH:MM format.

    Returns:
        A list of conflicting sqlite3.Row objects (empty list = no conflict).
    """
    sql = """
        SELECT id, customer_name, service_type, status
        FROM appointments
        WHERE appointment_date = ?
          AND appointment_time = ?
          AND status = 'Pending'
    """
    with get_connection() as conn:
        return conn.execute(sql, (appointment_date, appointment_time)).fetchall()


def get_todays_appointments() -> list:
    """
    Return all appointments scheduled for today (any status), ordered by time.

    Returns:
        A list of sqlite3.Row objects for today's date.
    """
    today = datetime.today().strftime("%d/%m/%Y")
    sql = """
        SELECT id, customer_name, service_type, appointment_date, appointment_time, status
        FROM appointments
        WHERE appointment_date = ?
        ORDER BY appointment_time
    """
    with get_connection() as conn:
        return conn.execute(sql, (today,)).fetchall()


def search_appointments(
    status: str = None,
    customer_name: str = None,
    date_from: str = None,
    date_to: str = None,
) -> list:
    """
    Search and filter appointments with optional criteria.

    All parameters are optional. Providing none returns all appointments
    (equivalent to get_all_appointments).

    Args:
        status:        Filter by status ('Pending', 'Completed', 'Cancelled').
        customer_name: Filter by partial customer name match (case-insensitive).
        date_from:     Show appointments on or after this date (DD/MM/YYYY).
        date_to:       Show appointments on or before this date (DD/MM/YYYY).

    Returns:
        A list of sqlite3.Row objects ordered by date and time.
    """
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if customer_name:
        conditions.append("LOWER(customer_name) LIKE ?")
        params.append(f"%{customer_name.lower()}%")

    # Date comparisons: convert DD/MM/YYYY to YYYY-MM-DD for correct SQLite ordering
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%d/%m/%Y").strftime("%Y-%m-%d")
            conditions.append("STRFTIME('%Y-%m-%d', SUBSTR(appointment_date,7,4)||'-'||SUBSTR(appointment_date,4,2)||'-'||SUBSTR(appointment_date,1,2)) >= ?")
            params.append(dt_from)
        except ValueError:
            pass  # Invalid date_from — ignore silently

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%d/%m/%Y").strftime("%Y-%m-%d")
            conditions.append("STRFTIME('%Y-%m-%d', SUBSTR(appointment_date,7,4)||'-'||SUBSTR(appointment_date,4,2)||'-'||SUBSTR(appointment_date,1,2)) <= ?")
            params.append(dt_to)
        except ValueError:
            pass  # Invalid date_to — ignore silently

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT id, customer_name, service_type, appointment_date, appointment_time, status
        FROM appointments
        {where}
        ORDER BY appointment_date, appointment_time
    """
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()
