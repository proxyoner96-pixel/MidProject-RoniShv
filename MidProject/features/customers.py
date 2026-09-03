"""
features/customers.py
======================
Business logic and database operations for Customer management.

This module contains ONLY logic and DB queries — no input() or print() calls.
All user interaction happens in ui.py.

Implements Bonus 1 (customer management portion):
  - add_customer         : add a new customer record
  - get_all_customers    : list all customers
  - get_customer_by_id   : look up a single customer (used by invoice.py and ui.py)
  - delete_customer      : remove a customer (cascades to invoices, nullifies appointment FK)
  - get_customer_history : return a customer's linked appointments and invoices
"""

from db import get_connection


def add_customer(name: str, phone: str = "", email: str = "", address: str = "", id_number: str = "") -> int:
    """
    Insert a new customer into the database.

    Args:
        name:      Customer's full name (required, non-empty).
        phone:     Phone number (optional).
        email:     Email address (optional).
        address:   Physical address (optional).
        id_number: Israeli ID card number, used for chatbot identity verification (optional).

    Returns:
        The integer ID of the newly created customer.

    Raises:
        ValueError: If name is empty.
    """
    if not name.strip():
        raise ValueError("Customer name cannot be empty.")

    sql = "INSERT INTO customers (name, phone, email, address, id_number) VALUES (?, ?, ?, ?, ?)"
    with get_connection() as conn:
        cursor = conn.execute(sql, (name.strip(), phone.strip(), email.strip(), address.strip(), id_number.strip()))
        return cursor.lastrowid


def get_all_customers() -> list:
    """
    Retrieve all customers from the database, ordered alphabetically by name.

    Returns:
        A list of sqlite3.Row objects.
    """
    sql = "SELECT id, name, phone, email, address, id_number FROM customers ORDER BY name"
    with get_connection() as conn:
        return conn.execute(sql).fetchall()


def get_customer_by_id(customer_id: int):
    """
    Retrieve a single customer by their ID.

    Args:
        customer_id: The integer ID of the customer.

    Returns:
        A sqlite3.Row if found, or None if no customer matches.
    """
    sql = "SELECT id, name, phone, email, address, id_number FROM customers WHERE id = ?"
    with get_connection() as conn:
        return conn.execute(sql, (customer_id,)).fetchone()


def search_customers_by_name(partial_name: str) -> list:
    """
    Search customers by partial, case-insensitive name match.

    Used by the chatbot's NLU layer: the user types a free-text name, and this
    returns every customer that could match, so the caller can decide whether
    the match is unique or needs a clarifying question (e.g. two "Ronit"s).

    Args:
        partial_name: A full or partial name to search for (non-empty).

    Returns:
        A list of sqlite3.Row objects (id, name, phone, email, address, id_number),
        ordered alphabetically. Empty list if nothing matches.
    """
    if not partial_name or not partial_name.strip():
        return []

    sql = """
        SELECT id, name, phone, email, address, id_number
        FROM customers
        WHERE LOWER(name) LIKE ?
        ORDER BY name
    """
    with get_connection() as conn:
        return conn.execute(sql, (f"%{partial_name.strip().lower()}%",)).fetchall()


def verify_identity(customer_id: int, claimed_id_number: str) -> bool:
    """
    Verify a claimed ID number against the stored value for a given customer.

    This is the ONLY function that should gate access to personal data
    (appointments, invoices, etc.) in the chatbot flow. A customer with no
    id_number on file can never be verified (fails closed, not open).

    Args:
        customer_id:       The candidate customer's ID.
        claimed_id_number: The ID number the user typed in the chat.

    Returns:
        True only if the customer exists, has an id_number on file, and it
        matches the claimed value exactly (after stripping whitespace).
    """
    customer = get_customer_by_id(customer_id)
    if customer is None:
        return False
    stored = (customer["id_number"] or "").strip()
    claimed = (claimed_id_number or "").strip()
    if not stored or not claimed:
        return False
    return stored == claimed


def delete_customer(customer_id: int) -> bool:
    """
    Delete a customer by their ID.

    Due to the FK constraints in schema.sql:
      - Their invoices are CASCADE-deleted automatically.
      - Their linked appointments keep the row but customer_id is SET NULL.

    Args:
        customer_id: The integer ID of the customer to delete.

    Returns:
        True if the customer was found and deleted, False otherwise.
    """
    sql = "DELETE FROM customers WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.execute(sql, (customer_id,))
        return cursor.rowcount > 0


def get_customer_history(customer_id: int) -> dict:
    """
    Return the full history for a customer: all their appointments and invoices.

    Args:
        customer_id: The integer ID of the customer.

    Returns:
        A dict with two keys:
          'appointments': list of sqlite3.Row  (service, date, time, status)
          'invoices':     list of sqlite3.Row  (invoice_number, amount, date)
    """
    appt_sql = """
        SELECT id, service_type, appointment_date, appointment_time, status
        FROM appointments
        WHERE customer_id = ?
        ORDER BY appointment_date, appointment_time
    """
    inv_sql = """
        SELECT id, invoice_number, amount, invoice_date
        FROM invoices
        WHERE customer_id = ?
        ORDER BY invoice_date
    """
    with get_connection() as conn:
        appointments = conn.execute(appt_sql, (customer_id,)).fetchall()
        invoices = conn.execute(inv_sql, (customer_id,)).fetchall()

    return {"appointments": appointments, "invoices": invoices}
