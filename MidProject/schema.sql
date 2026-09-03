-- schema.sql
-- ============================================================
-- Database Schema for the Appointments Management System.
-- Defines all tables: customers, appointments, invoices, leads,
-- including primary keys (PRIMARY KEY) and foreign keys (FOREIGN KEY).
-- This file is loaded automatically by db.py via init_db() on every run.
-- We use IF NOT EXISTS so existing data is never overwritten on restart.
-- ============================================================

-- Customers table (Bonus 1 — Customer Management)
-- id_number: Israeli ID card number (תעודת זהות), used ONLY for identity
-- verification in the chatbot layer — never exposed before a successful match.
CREATE TABLE IF NOT EXISTS customers (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    phone     TEXT,
    email     TEXT,
    address   TEXT,
    id_number TEXT
);

-- Appointments table — core of the project (mandatory requirement)
-- customer_id is an optional foreign key to customers.
-- A standalone appointment (no linked customer) is supported for the core flow.
-- ON DELETE SET NULL: if the customer is deleted, the appointment is kept but unlinked.
CREATE TABLE IF NOT EXISTS appointments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id      INTEGER,
    customer_name    TEXT NOT NULL,
    service_type     TEXT NOT NULL,
    appointment_date TEXT NOT NULL,   -- format: DD/MM/YYYY
    appointment_time TEXT NOT NULL,   -- format: HH:MM
    status           TEXT NOT NULL DEFAULT 'Pending',  -- Pending / Completed / Cancelled
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL
);

-- Invoices table (Bonus 1 — Customer Management)
-- ON DELETE CASCADE: deleting a customer also removes all their invoices
-- (invoices without a customer have no business meaning).
CREATE TABLE IF NOT EXISTS invoices (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id    INTEGER NOT NULL,
    invoice_number TEXT    UNIQUE NOT NULL,
    amount         REAL    NOT NULL,
    invoice_date   TEXT    NOT NULL,   -- format: DD/MM/YYYY
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

-- Leads table (Bonus 2 — Lead Management)
CREATE TABLE IF NOT EXISTS leads (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    phone  TEXT,
    source TEXT,                              -- e.g. Facebook, Referral, Website
    status TEXT NOT NULL DEFAULT 'New',       -- New / In Progress / Converted / Rejected
    notes  TEXT
);
