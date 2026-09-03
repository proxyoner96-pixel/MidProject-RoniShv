"""
db.py
=====
Handles all SQLite database connectivity for the Appointments Management System.

Responsibilities:
  - DB_PATH: single constant defining where the database file lives.
  - get_connection(): opens a connection with foreign keys enforced and
    row_factory set so rows behave like dictionaries.
  - init_db(): reads schema.sql and creates all tables if they don't exist yet.
"""

import sqlite3
import os

# Path to the SQLite database file.
# Located in the same directory as this file.
DB_PATH = os.path.join(os.path.dirname(__file__), "appointments.db")

# Path to the SQL schema file (relative to this file).
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.

    Settings applied to every connection:
      - PRAGMA foreign_keys = ON  : enforce ON DELETE CASCADE / SET NULL rules.
      - row_factory = sqlite3.Row : rows are accessible by column name (like dicts).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_customers_id_number_column(conn: sqlite3.Connection) -> None:
    """
    Defensive migration: guarantee `customers.id_number` exists.

    `CREATE TABLE IF NOT EXISTS` (used below) does nothing to a table that
    already exists — so if an older copy of appointments.db (from before the
    chatbot's identity-verification feature) is ever restored, re-synced, or
    checked out on top of the current schema.sql, the app would crash with
    "no such column: id_number" instead of just... having the column. This
    function makes startup self-healing regardless of which appointments.db
    happens to be on disk.
    """
    columns = [row[1] for row in conn.execute("PRAGMA table_info(customers)").fetchall()]
    if "id_number" not in columns:
        conn.execute("ALTER TABLE customers ADD COLUMN id_number TEXT")

    # Backfill any customer left without an id_number (e.g. rows that existed
    # before this column was added) so identity verification always has
    # something concrete to check, instead of every such customer being
    # permanently unverifiable.
    conn.execute(
        "UPDATE customers SET id_number = printf('900%06d', id) "
        "WHERE id_number IS NULL OR TRIM(id_number) = ''"
    )


def init_db() -> None:
    """
    Read schema.sql and execute it to create all tables (IF NOT EXISTS),
    then run any small defensive migrations for columns added after the
    original schema (see _ensure_customers_id_number_column).
    Called once at startup from main.py / the chatbot's app.py.
    """
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    with get_connection() as conn:
        conn.executescript(schema)
        _ensure_customers_id_number_column(conn)
        conn.commit()
