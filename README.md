# MidProject-RoniShv
# Appointments Management System
> **Mid-Course Python Project** — A robust, modular CLI appointment and CRM management system built with Python and SQLite.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

The **Appointments Management System** is a general-purpose, command-line interface (CLI) application developed to streamline business scheduling, customer relationship management (CRM), and invoicing. 

Built entirely with standard library tools, the system persists all operational data to a relational SQLite database. Its architecture strictly separates business logic, data persistence, and user presentation, ensuring high maintainability and full adaptability for any business domain via lightweight configuration.

---

## Key Features

- **End-to-End Appointment Scheduling**: Add, view, update, cancel, and delete appointments with real-time schedule conflict detection.
- **Customer & CRM Management**: Full Customer Lifecycle tracking with customer history, contact details, and linked records.
- **Lead Tracking & Automated Conversion**: Manage prospect pipelines and convert qualified leads into full customer accounts with a single command.
- **Automated Invoicing**: Auto-incrementing, collision-free invoice generation (`INV-0001`, `INV-0002`, ...) linked via foreign keys.
- **Strict Data Integrity**: Full schema validation, business hour enforcement, and foreign key cascades.

---

## Project Structure

```text
MidProject/
├── main.py                 # Application entry point & configuration
├── Business.py             # Domain model holding business metadata & rules
├── db.py                   # Database connection manager (enforces PRAGMAs)
├── schema.sql              # Relational database DDL schema definitions
├── ui.py                   # Terminal UI, menus, ANSI stylers, & user input handlers
└── features/               # Modular feature package (Pure Business Logic)
    ├── __init__.py
    ├── appointments.py     # Appointment CRUD & conflict resolution logic
    ├── customers.py        # Customer CRUD & appointment/invoice history
    ├── invoice.py          # Sequential invoice generator & ledger
    └── leads.py            # Lead lifecycle & customer conversion workflows
