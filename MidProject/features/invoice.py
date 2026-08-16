"""
features/invoice.py
====================
Business logic and database operations for Invoice management.

This module contains ONLY logic and DB queries — no input() or print() calls.
All user interaction happens in ui.py.

Implements Bonus 1 (invoice portion):
  - create_invoice             : generate a new invoice with a unique auto-number
  - get_invoices_by_customer   : list all invoices for a specific customer

Invoice numbers are auto-generated in the format INV-0001, INV-0002, etc.,
ensuring uniqueness without requiring user input.
"""

from datetime import datetime
from db import get_connection


def _next_invoice_number(conn) -> str:
    """
    Generate the next sequential invoice number.

    Queries the invoices table for the highest existing invoice_number,
    increments it, and returns a zero-padded string like 'INV-0042'.

    Args:
        conn: An open sqlite3.Connection.

    Returns:
        A unique invoice number string (e.g. 'INV-0001').
    """
    row = conn.execute("SELECT MAX(invoice_number) FROM invoices").fetchone()
    last = row[0]  # e.g. 'INV-0007' or None if table is empty

    if last is None:
        next_num = 1
    else:
        # Extract the numeric part after 'INV-'
        next_num = int(last.split("-")[1]) + 1

    return f"INV-{next_num:04d}"


def create_invoice(customer_id: int, amount: float) -> dict:
    """
    Create a new invoice for a customer.

    Args:
        customer_id: The integer ID of the customer (must exist in the DB).
        amount:      The invoice amount (must be positive).

    Returns:
        A dict with keys: invoice_number, amount, invoice_date, customer_id.

    Raises:
        ValueError: If amount is not positive, or if customer_id doesn't exist.
    """
    if amount <= 0:
        raise ValueError("Invoice amount must be greater than zero.")

    today = datetime.today().strftime("%d/%m/%Y")

    with get_connection() as conn:
        # Verify the customer exists
        customer = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not customer:
            raise ValueError(f"No customer found with ID {customer_id}.")

        invoice_number = _next_invoice_number(conn)

        conn.execute(
            "INSERT INTO invoices (customer_id, invoice_number, amount, invoice_date) VALUES (?, ?, ?, ?)",
            (customer_id, invoice_number, amount, today),
        )

    return {
        "invoice_number": invoice_number,
        "amount": amount,
        "invoice_date": today,
        "customer_id": customer_id,
    }


def get_invoices_by_customer(customer_id: int) -> list:
    """
    Retrieve all invoices for a specific customer, ordered by date.

    Args:
        customer_id: The integer ID of the customer.

    Returns:
        A list of sqlite3.Row objects (id, invoice_number, amount, invoice_date).
    """
    sql = """
        SELECT id, invoice_number, amount, invoice_date
        FROM invoices
        WHERE customer_id = ?
        ORDER BY invoice_date
    """
    with get_connection() as conn:
        return conn.execute(sql, (customer_id,)).fetchall()
