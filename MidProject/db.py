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


def init_db() -> None:
    """
    Read schema.sql and execute it to create all tables (IF NOT EXISTS).
    Called once at startup from main.py before the menus are shown.
    """
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    with get_connection() as conn:
        conn.executescript(schema)
