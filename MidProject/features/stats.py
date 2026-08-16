"""
features/stats.py
==================
Statistics and revenue reporting for the Appointments Management System.

This module contains ONLY DB queries — no input() or print() calls.
All display logic lives in ui.py.

Functions:
  - get_dashboard_stats    : headline numbers shown at startup
  - get_revenue_by_customer: revenue total per customer
  - get_revenue_by_service : revenue total per service type
  - get_revenue_by_month   : revenue total per calendar month
"""

from db import get_connection
from datetime import datetime


def get_dashboard_stats() -> dict:
    """
    Return headline statistics for the startup dashboard.

    Returns a dict with the following keys:
      total_appointments  (int)
      pending             (int)
      completed           (int)
      cancelled           (int)
      todays_count        (int)   — appointments scheduled for today
      total_customers     (int)
      total_leads         (int)
      total_revenue       (float) — sum of all invoice amounts
      top_service         (str | None) — most-booked service type
    """
    today = datetime.today().strftime("%d/%m/%Y")

    with get_connection() as conn:
        total_appts = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        pending     = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Pending'").fetchone()[0]
        completed   = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Completed'").fetchone()[0]
        cancelled   = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Cancelled'").fetchone()[0]
        todays      = conn.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date=?", (today,)).fetchone()[0]
        total_custs = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        revenue_row = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices").fetchone()
        total_revenue = float(revenue_row[0])

        # Top service: service type with the most appointments (any status)
        top_row = conn.execute("""
            SELECT service_type, COUNT(*) AS cnt
            FROM appointments
            GROUP BY service_type
            ORDER BY cnt DESC
            LIMIT 1
        """).fetchone()
        top_service = top_row["service_type"] if top_row else None

    return {
        "total_appointments": total_appts,
        "pending":            pending,
        "completed":          completed,
        "cancelled":          cancelled,
        "todays_count":       todays,
        "total_customers":    total_custs,
        "total_leads":        total_leads,
        "total_revenue":      total_revenue,
        "top_service":        top_service,
    }


def get_revenue_by_customer() -> list:
    """
    Return total invoice revenue grouped by customer, highest first.

    Returns:
        List of sqlite3.Row with columns: name, total_revenue, invoice_count.
    """
    sql = """
        SELECT c.name, 
               COALESCE(SUM(i.amount), 0) AS total_revenue,
               COUNT(i.id)                AS invoice_count
        FROM customers c
        LEFT JOIN invoices i ON i.customer_id = c.id
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC
    """
    with get_connection() as conn:
        return conn.execute(sql).fetchall()


def get_revenue_by_service() -> list:
    """
    Return total revenue per service type (based on appointment service + invoice amounts).

    Since invoices are linked to customers (not directly to appointments), this
    query approximates by distributing each customer's total invoiced amount
    equally across their service types. A simpler and more honest approach is
    to count completed appointments per service and show the appointment revenue
    as a proxy — that is what we do here.

    Returns:
        List of sqlite3.Row with columns: service_type, appointment_count, completed_count.
    """
    sql = """
        SELECT service_type,
               COUNT(*)                                           AS appointment_count,
               SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed_count,
               SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled_count
        FROM appointments
        GROUP BY service_type
        ORDER BY appointment_count DESC
    """
    with get_connection() as conn:
        return conn.execute(sql).fetchall()


def get_revenue_by_month() -> list:
    """
    Return total invoiced revenue grouped by year-month, oldest first.

    Returns:
        List of sqlite3.Row with columns: month_label (e.g. '08/2026'), total_revenue, invoice_count.
    """
    sql = """
        SELECT SUBSTR(invoice_date, 4, 2) || '/' || SUBSTR(invoice_date, 7, 4) AS month_label,
               SUM(amount)   AS total_revenue,
               COUNT(id)     AS invoice_count
        FROM invoices
        GROUP BY month_label
        ORDER BY SUBSTR(invoice_date, 7, 4), SUBSTR(invoice_date, 4, 2)
    """
    with get_connection() as conn:
        return conn.execute(sql).fetchall()
