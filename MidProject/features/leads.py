"""
features/leads.py
==================
Business logic and database operations for Lead management.

This module contains ONLY logic and DB queries — no input() or print() calls.
All user interaction happens in ui.py.

Implements Bonus 2 (lead management):
  - add_lead                : create a new lead record
  - get_all_leads           : list all leads
  - update_lead_status      : change a lead's status
  - delete_lead             : remove a lead
  - convert_lead_to_customer: promote a lead to a full customer record
"""

from db import get_connection
from features.customers import add_customer

# Allowed lead status values.
LEAD_STATUS_OPTIONS = ["New", "In Progress", "Converted", "Rejected"]


def add_lead(name: str, phone: str = "", source: str = "", notes: str = "") -> int:
    """
    Insert a new lead into the database.

    Args:
        name:   Lead's full name (required, non-empty).
        phone:  Phone number (optional).
        source: Where the lead came from, e.g. 'Facebook', 'Referral' (optional).
        notes:  Free-text notes about the lead (optional).

    Returns:
        The integer ID of the newly created lead.

    Raises:
        ValueError: If name is empty.
    """
    if not name.strip():
        raise ValueError("Lead name cannot be empty.")

    sql = "INSERT INTO leads (name, phone, source, status, notes) VALUES (?, ?, ?, 'New', ?)"
    with get_connection() as conn:
        cursor = conn.execute(sql, (name.strip(), phone.strip(), source.strip(), notes.strip()))
        return cursor.lastrowid


def get_all_leads() -> list:
    """
    Retrieve all leads from the database, ordered by status then name.

    Returns:
        A list of sqlite3.Row objects.
    """
    sql = "SELECT id, name, phone, source, status, notes FROM leads ORDER BY status, name"
    with get_connection() as conn:
        return conn.execute(sql).fetchall()


def update_lead_status(lead_id: int, new_status: str) -> bool:
    """
    Update the status of an existing lead.

    Args:
        lead_id:    The integer ID of the lead.
        new_status: The new status. Must be one of LEAD_STATUS_OPTIONS.

    Returns:
        True if the lead was found and updated, False if no row matched.

    Raises:
        ValueError: If new_status is not in LEAD_STATUS_OPTIONS.
    """
    if new_status not in LEAD_STATUS_OPTIONS:
        raise ValueError(
            f"Invalid status '{new_status}'. Choose from: {', '.join(LEAD_STATUS_OPTIONS)}"
        )
    sql = "UPDATE leads SET status = ? WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.execute(sql, (new_status, lead_id))
        return cursor.rowcount > 0


def delete_lead(lead_id: int) -> bool:
    """
    Delete a lead by its ID.

    Args:
        lead_id: The integer ID of the lead to delete.

    Returns:
        True if the lead was found and deleted, False otherwise.
    """
    sql = "DELETE FROM leads WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.execute(sql, (lead_id,))
        return cursor.rowcount > 0


def convert_lead_to_customer(lead_id: int) -> int:
    """
    Convert a lead to a full customer record.

    Steps:
      1. Fetch the lead by ID.
      2. Create a new customer using the lead's name and phone.
      3. Update the lead's status to 'Converted'.

    Args:
        lead_id: The integer ID of the lead to convert.

    Returns:
        The integer ID of the newly created customer.

    Raises:
        ValueError: If no lead with the given ID exists, or if the lead is
                    already Converted or Rejected.
    """
    with get_connection() as conn:
        lead = conn.execute(
            "SELECT id, name, phone, status FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()

    if not lead:
        raise ValueError(f"No lead found with ID {lead_id}.")
    if lead["status"] == "Converted":
        raise ValueError(f"Lead #{lead_id} has already been converted to a customer.")
    if lead["status"] == "Rejected":
        raise ValueError(f"Lead #{lead_id} is marked as Rejected and cannot be converted.")

    # Create the customer from lead data (phone only; email/address unknown at lead stage)
    new_customer_id = add_customer(name=lead["name"], phone=lead["phone"])

    # Mark the lead as Converted
    with get_connection() as conn:
        conn.execute("UPDATE leads SET status = 'Converted' WHERE id = ?", (lead_id,))

    return new_customer_id
