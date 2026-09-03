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

## Final Project — Verification & Appointments Chatbot

`Chatbot/` adds a natural-language web chatbot on top of this exact codebase (no new
CRUD, no duplicate data access): a customer types a free-text sentence, the bot
identifies them, verifies their ID number against the real record, and reports their
real appointment — correcting them if they misremembered the date. See
[`Chatbot/README.md`](Chatbot/README.md) for how it works,
[`DEPLOY.md`](DEPLOY.md) for running it locally or deploying it, and
[`demo/chatbot_demo.mp4`](demo/chatbot_demo.mp4) for a recorded end-to-end walkthrough.

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

Chatbot/
├── app.py                  # Flask server (chat page + /api/chat + /api/reset)
├── conversation.py         # Conversation state machine — identify → confirm → verify → answer
├── nlu.py                  # Gemini-based free-text extraction (name + claimed date)
├── reply_builder.py        # Final natural-language reply, with real-data date comparison
├── gemini_client.py        # Single wrapper around the Gemini API (google-genai SDK)
└── templates/index.html    # Chat UI
