"""
ui.py
=====
All user interaction for the Appointments Management System lives here.

This is the ONLY file that calls input() and print(). All feature modules
(features/appointments.py, features/customers.py, etc.) contain pure logic
and DB queries with no knowledge of how the UI works.

Contents:
  1. ANSI color constants
  2. Low-level helpers: clear_screen, color wrappers, print_table
  3. Input helpers: input_nonempty, input_date, input_time, input_int, input_positive_float
  4. Appointment flows: menu_appointments + all sub-flows
     (add, view all, update status, delete, today's view, search & filter)
  5. Customer & Invoice flows: menu_customers + all sub-flows
  6. Lead flows: menu_leads + all sub-flows
  7. Business Info screen
  8. Statistics & Reports: dashboard, revenue report
  9. Top-level: menu_main (entry point called from main.py)
"""

import os
from datetime import datetime

from Business import Business
from features import appointments, customers, invoice, leads
from features import stats


# ─────────────────────────────────────────────────────────────────────────────
# 1. ANSI Color Constants
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
WHITE  = "\033[97m"
DIM    = "\033[2m"


def c(text: str, color: str) -> str:
    """Wrap text with an ANSI color code and reset at the end."""
    return f"{color}{text}{RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Low-level UI Helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_screen() -> None:
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    """Print a styled cyan section header."""
    width = 46
    border = c("═" * width, CYAN)
    print(f"\n{border}")
    print(c(f"  {title}", CYAN + BOLD))
    print(f"{border}")


def print_box_menu(title: str, options: list) -> None:
    """
    Print a box-drawn menu.

    Args:
        title:   Title displayed in the menu header.
        options: List of strings for each menu option (already formatted, e.g. "1. Add New").
    """
    width = 44
    top    = c("╔" + "═" * width + "╗", CYAN)
    bottom = c("╚" + "═" * width + "╝", CYAN)
    sep    = c("╠" + "═" * width + "╣", CYAN)
    side   = c("║", CYAN)

    def row(content: str) -> str:
        padded = content.ljust(width)
        return f"{side} {padded}{side}"

    print(f"\n{top}")
    print(row(c(title.center(width - 1), BOLD + CYAN)))
    print(sep)
    print(row(""))
    for opt in options:
        print(row(opt))
    print(row(""))
    print(bottom)


def print_success(msg: str) -> None:
    """Print a green success message."""
    print(c(f"\n  ✔ {msg}", GREEN))


def print_error(msg: str) -> None:
    """Print a red error message."""
    print(c(f"  ✘ Error: {msg}", RED))


def print_warning(msg: str) -> None:
    """Print a yellow warning message."""
    print(c(f"\n  ⚠ WARNING: {msg}", YELLOW))


def print_table(rows: list, columns: list, headers: list = None) -> None:
    """
    Print a formatted ASCII table.

    Args:
        rows:    List of sqlite3.Row objects (or dicts) to display.
        columns: List of column key names to extract from each row.
        headers: Optional list of display header labels. Defaults to columns.
    """
    if headers is None:
        headers = [col.replace("_", " ").title() for col in columns]

    if not rows:
        print(c("  (no records found)", DIM))
        return

    # Convert rows to list of lists of strings
    data = []
    for row in rows:
        data.append([str(row[col]) if row[col] is not None else "" for col in columns])

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row_data in data:
        for i, cell in enumerate(row_data):
            # Truncate long cells to keep table readable
            display = cell if len(cell) <= 22 else cell[:20] + "…"
            col_widths[i] = max(col_widths[i], len(display))

    def make_row(cells: list) -> str:
        parts = [f" {cells[i].ljust(col_widths[i])} " for i in range(len(cells))]
        return "|" + "|".join(parts) + "|"

    def make_divider() -> str:
        parts = ["-" * (col_widths[i] + 2) for i in range(len(col_widths))]
        return "+" + "+".join(parts) + "+"

    divider = make_divider()
    print(c(divider, DIM))
    print(c(make_row(headers), CYAN + BOLD))
    print(c(divider, DIM))
    for row_data in data:
        # Truncate long cells
        display_cells = [cell if len(cell) <= 22 else cell[:20] + "…" for cell in row_data]
        print(make_row(display_cells))
    print(c(divider, DIM))
    print(c(f"  Total: {len(rows)} record(s)", DIM))


def pause() -> None:
    """Wait for the user to press Enter before continuing."""
    input(c("\n  Press Enter to continue...", DIM))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Input Helpers
# ─────────────────────────────────────────────────────────────────────────────

def input_nonempty(prompt: str) -> str:
    """
    Prompt the user until they enter a non-empty string.

    Returns:
        A stripped, non-empty string.
    """
    while True:
        value = input(f"  {prompt}").strip()
        if value:
            return value
        print_error("This field cannot be empty. Please try again.")


def input_optional(prompt: str) -> str:
    """
    Prompt the user for an optional field. Returns empty string if skipped.

    Returns:
        A stripped string (may be empty).
    """
    return input(f"  {prompt}").strip()


def input_date(prompt: str) -> str:
    """
    Prompt the user for a date in DD/MM/YYYY format, validating with datetime.

    Returns:
        A valid date string in DD/MM/YYYY format.
    """
    while True:
        value = input(f"  {prompt}").strip()
        try:
            datetime.strptime(value, "%d/%m/%Y")
            return value
        except ValueError:
            print_error("Invalid date. Please use the format DD/MM/YYYY (e.g. 25/12/2026).")


def input_time(prompt: str) -> str:
    """
    Prompt the user for a time in HH:MM format, validating with datetime.

    Returns:
        A valid time string in HH:MM format.
    """
    while True:
        value = input(f"  {prompt}").strip()
        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            print_error("Invalid time. Please use the format HH:MM (e.g. 14:30).")


def input_int(prompt: str) -> int:
    """
    Prompt the user for an integer ID, looping until a valid number is entered.

    Returns:
        A positive integer.
    """
    while True:
        value = input(f"  {prompt}").strip()
        if value.isdigit() and int(value) > 0:
            return int(value)
        print_error("Please enter a valid numeric ID (positive integer).")


def input_positive_float(prompt: str) -> float:
    """
    Prompt the user for a positive floating-point number (e.g. invoice amount).

    Returns:
        A positive float.
    """
    while True:
        value = input(f"  {prompt}").strip()
        try:
            amount = float(value)
            if amount > 0:
                return amount
            print_error("Amount must be greater than zero.")
        except ValueError:
            print_error("Please enter a valid number (e.g. 150 or 99.50).")


def input_service(business: Business) -> str:
    """
    Prompt the user to pick a service from the business's service list.

    Displays a numbered list and validates the choice.

    Returns:
        The selected service name string.
    """
    services = business.services
    print(c(f"\n  Available services:", CYAN))
    for i, svc in enumerate(services, 1):
        print(f"    {i}. {svc}")
    while True:
        value = input("  Select service number: ").strip()
        if value.isdigit() and 1 <= int(value) <= len(services):
            return services[int(value) - 1]
        print_error(f"Please enter a number between 1 and {len(services)}.")


def input_status(prompt: str, options: list) -> str:
    """
    Prompt the user to select a status from a predefined list.
    Supports selecting by option number (1, 2, 3...) or by status name (case-insensitive).

    Returns:
        A valid status string from options.
    """
    print(c("\n  Available statuses:", CYAN))
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        value = input(f"  {prompt}").strip()
        if value.isdigit() and 1 <= int(value) <= len(options):
            return options[int(value) - 1]
        for opt in options:
            if value.lower() == opt.lower():
                return opt
        print_error(f"Invalid status. Please select a number (1-{len(options)}) or enter a status name.")


def confirm(prompt: str) -> bool:
    """
    Ask a yes/no confirmation question.

    Returns:
        True if user enters 'y', False if 'n' (loops on other input).
    """
    while True:
        answer = input(c(f"\n  {prompt} (y/n): ", YELLOW)).strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        print_error("Please enter 'y' for yes or 'n' for no.")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Appointment Flows
# ─────────────────────────────────────────────────────────────────────────────

def _flow_add_appointment(business: Business) -> None:
    """Flow: collect inputs and add a new appointment."""
    print_header("Add New Appointment")

    name = input_nonempty("Customer name: ")
    service = input_service(business)
    date = input_date("Date (DD/MM/YYYY): ")

    # Time: validate format AND working hours
    while True:
        time = input_time("Time (HH:MM): ")
        if business.is_within_hours(time):
            break
        print_error(
            f"Time {time} is outside working hours "
            f"({business.working_hours['start']} – {business.working_hours['end']})."
        )

    # Conflict detection (bonus advantage)
    conflicts = appointments.check_conflict(date, time)
    if conflicts:
        print_warning(
            f"There is already an active appointment at {date} {time}.\n"
            f"  Existing: {conflicts[0]['customer_name']} — "
            f"{conflicts[0]['service_type']} (Status: {conflicts[0]['status']})"
        )
        if not confirm("Add this appointment anyway?"):
            print(c("  ✘ Appointment creation cancelled.", RED))
            return

    new_id = appointments.add_appointment(name, service, date, time)
    print_success(f"Appointment added successfully! ID: {new_id}")


def _flow_view_appointments() -> None:
    """Flow: display all appointments in a table."""
    print_header("All Appointments")
    rows = appointments.get_all_appointments()
    print_table(
        rows,
        columns=["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
        headers=["ID", "Customer", "Service", "Date", "Time", "Status"],
    )
    pause()


def _flow_update_appointment_status() -> None:
    """Flow: show appointments table, then update status of a chosen appointment."""
    print_header("Update Appointment Status")
    rows = appointments.get_all_appointments()
    print_table(
        rows,
        columns=["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
        headers=["ID", "Customer", "Service", "Date", "Time", "Status"],
    )
    if not rows:
        pause()
        return

    appt_id = input_int("Enter appointment ID to update: ")
    new_status = input_status("New status: ", appointments.STATUS_OPTIONS)

    try:
        found = appointments.update_status(appt_id, new_status)
        if found:
            print_success(f"Appointment #{appt_id} status updated to \"{new_status}\".")
        else:
            print_error(f"No appointment found with ID {appt_id}.")
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_delete_appointment() -> None:
    """Flow: show appointments table, then delete a chosen appointment."""
    print_header("Delete Appointment")
    rows = appointments.get_all_appointments()
    print_table(
        rows,
        columns=["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
        headers=["ID", "Customer", "Service", "Date", "Time", "Status"],
    )
    if not rows:
        pause()
        return

    appt_id = input_int("Enter appointment ID to delete: ")
    if confirm(f"Are you sure you want to delete appointment #{appt_id}?"):
        found = appointments.delete_appointment(appt_id)
        if found:
            print_success(f"Appointment #{appt_id} deleted successfully.")
        else:
            print_error(f"No appointment found with ID {appt_id}.")
    else:
        print(c("  Deletion cancelled.", DIM))

    pause()


def _flow_view_todays_appointments() -> None:
    """Flow: display appointments scheduled for today."""
    print_header("Today's Appointments")
    rows = appointments.get_todays_appointments()
    if not rows:
        print(c("\n  No appointments scheduled for today.", DIM))
    else:
        print_table(
            rows,
            columns=["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
            headers=["ID", "Customer", "Service", "Date", "Time", "Status"],
        )
    pause()


def _flow_search_appointments() -> None:
    """Flow: filter appointments by status, date range, or customer name."""
    print_header("Search & Filter Appointments")
    print(c("  Leave any field empty to skip that filter.", DIM))

    # Status filter
    print(c(f"\n  Status options: {', '.join(appointments.STATUS_OPTIONS)} (or leave empty for all)", CYAN))
    status_input = input("  Filter by status: ").strip()
    status = status_input if status_input in appointments.STATUS_OPTIONS else None
    if status_input and not status:
        print_error(f"Unknown status '{status_input}' — ignoring.")

    # Customer name filter
    name_input = input("  Filter by customer name (partial match): ").strip()
    name_filter = name_input if name_input else None

    # Date range filter
    print(c("  Date range (DD/MM/YYYY). Leave empty to skip.", CYAN))
    date_from = None
    date_to   = None
    from_raw = input("  From date: ").strip()
    if from_raw:
        try:
            datetime.strptime(from_raw, "%d/%m/%Y")
            date_from = from_raw
        except ValueError:
            print_error(f"Invalid date '{from_raw}' — ignoring.")
    to_raw = input("  To date:   ").strip()
    if to_raw:
        try:
            datetime.strptime(to_raw, "%d/%m/%Y")
            date_to = to_raw
        except ValueError:
            print_error(f"Invalid date '{to_raw}' — ignoring.")

    print()
    rows = appointments.search_appointments(
        status=status,
        customer_name=name_filter,
        date_from=date_from,
        date_to=date_to,
    )

    # Show active filters summary
    active = []
    if status:      active.append(f"status={status}")
    if name_filter: active.append(f"name contains '{name_filter}'")
    if date_from:   active.append(f"from {date_from}")
    if date_to:     active.append(f"to {date_to}")
    if active:
        print(c(f"  Active filters: {', '.join(active)}", YELLOW))
    else:
        print(c("  No filters applied — showing all appointments.", DIM))

    print_table(
        rows,
        columns=["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
        headers=["ID", "Customer", "Service", "Date", "Time", "Status"],
    )
    pause()


def menu_appointments(business: Business) -> None:
    """Appointments sub-menu loop."""
    while True:
        clear_screen()
        print_box_menu("Manage Appointments", [
            "  1.  Add New Appointment",
            "  2.  View All Appointments",
            "  3.  Update Appointment Status",
            "  4.  Delete Appointment",
            "  5.  Today's Appointments",
            "  6.  Search & Filter",
            "  0.  Back to Main Menu",
        ])
        choice = input(c("\n  Select an option: ", YELLOW)).strip()

        if choice == "1":
            clear_screen()
            _flow_add_appointment(business)
            pause()
        elif choice == "2":
            clear_screen()
            _flow_view_appointments()
        elif choice == "3":
            clear_screen()
            _flow_update_appointment_status()
        elif choice == "4":
            clear_screen()
            _flow_delete_appointment()
        elif choice == "5":
            clear_screen()
            _flow_view_todays_appointments()
        elif choice == "6":
            clear_screen()
            _flow_search_appointments()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice. Please enter a number from the menu.")
            pause()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Customer & Invoice Flows
# ─────────────────────────────────────────────────────────────────────────────

def _flow_add_customer() -> None:
    """Flow: collect inputs and add a new customer."""
    print_header("Add New Customer")
    name    = input_nonempty("Name: ")
    phone   = input_optional("Phone (optional, press Enter to skip): ")
    email   = input_optional("Email (optional, press Enter to skip): ")
    address = input_optional("Address (optional, press Enter to skip): ")

    try:
        new_id = customers.add_customer(name, phone, email, address)
        print_success(f"Customer added successfully! ID: {new_id}")
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_view_customers() -> None:
    """Flow: display all customers in a table."""
    print_header("All Customers")
    rows = customers.get_all_customers()
    print_table(
        rows,
        columns=["id", "name", "phone", "email", "address"],
        headers=["ID", "Name", "Phone", "Email", "Address"],
    )
    pause()


def _flow_delete_customer() -> None:
    """Flow: show customers table, then delete a chosen customer."""
    print_header("Delete Customer")
    rows = customers.get_all_customers()
    print_table(rows, columns=["id", "name", "phone"], headers=["ID", "Name", "Phone"])
    if not rows:
        pause()
        return

    cust_id = input_int("Enter customer ID to delete: ")
    customer = customers.get_customer_by_id(cust_id)
    if not customer:
        print_error(f"No customer found with ID {cust_id}.")
        pause()
        return

    print_warning(
        "Deleting this customer will also delete all their invoices.\n"
        "  Linked appointments will be kept but unlinked from this customer."
    )
    if confirm(f"Are you sure you want to delete \"{customer['name']}\" (ID: {cust_id})?"):
        customers.delete_customer(cust_id)
        print_success(f"Customer #{cust_id} ({customer['name']}) deleted successfully.")
    else:
        print(c("  Deletion cancelled.", DIM))

    pause()


def _flow_create_invoice() -> None:
    """Flow: show customers table, then create an invoice for a chosen customer."""
    print_header("Create Invoice")
    rows = customers.get_all_customers()
    print_table(rows, columns=["id", "name", "phone"], headers=["ID", "Name", "Phone"])
    if not rows:
        pause()
        return

    cust_id = input_int("Enter customer ID: ")
    customer = customers.get_customer_by_id(cust_id)
    if not customer:
        print_error(f"No customer found with ID {cust_id}.")
        pause()
        return

    amount = input_positive_float("Invoice amount (ILS): ")

    try:
        result = invoice.create_invoice(cust_id, amount)
        print_success("Invoice created successfully!")
        print(f"\n  {c('Invoice Number:', CYAN)} {result['invoice_number']}")
        print(f"  {c('Customer:      ', CYAN)} {customer['name']}")
        print(f"  {c('Amount:        ', CYAN)} {result['amount']:.2f} ILS")
        print(f"  {c('Date:          ', CYAN)} {result['invoice_date']}")
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_customer_history() -> None:
    """Flow: show customers table, then display full history for a chosen customer."""
    print_header("Customer History")
    rows = customers.get_all_customers()
    print_table(rows, columns=["id", "name", "phone"], headers=["ID", "Name", "Phone"])
    if not rows:
        pause()
        return

    cust_id = input_int("Enter customer ID: ")
    customer = customers.get_customer_by_id(cust_id)
    if not customer:
        print_error(f"No customer found with ID {cust_id}.")
        pause()
        return

    history = customers.get_customer_history(cust_id)

    print(f"\n{c('  ─── Appointments for:', CYAN)} {c(customer['name'], BOLD)}")
    print_table(
        history["appointments"],
        columns=["id", "service_type", "appointment_date", "appointment_time", "status"],
        headers=["ID", "Service", "Date", "Time", "Status"],
    )

    print(f"\n{c('  ─── Invoices for:', CYAN)} {c(customer['name'], BOLD)}")
    print_table(
        history["invoices"],
        columns=["id", "invoice_number", "amount", "invoice_date"],
        headers=["ID", "Invoice #", "Amount (ILS)", "Date"],
    )

    pause()


def menu_customers() -> None:
    """Customers & Invoices sub-menu loop."""
    while True:
        clear_screen()
        print_box_menu("Manage Customers & Invoices", [
            "  1.  Add New Customer",
            "  2.  View All Customers",
            "  3.  Delete Customer",
            "  4.  Create Invoice for Customer",
            "  5.  View Customer History",
            "  0.  Back to Main Menu",
        ])
        choice = input(c("\n  Select an option: ", YELLOW)).strip()

        if choice == "1":
            clear_screen()
            _flow_add_customer()
        elif choice == "2":
            clear_screen()
            _flow_view_customers()
        elif choice == "3":
            clear_screen()
            _flow_delete_customer()
        elif choice == "4":
            clear_screen()
            _flow_create_invoice()
        elif choice == "5":
            clear_screen()
            _flow_customer_history()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice. Please enter a number from the menu.")
            pause()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Lead Flows
# ─────────────────────────────────────────────────────────────────────────────

def _flow_add_lead() -> None:
    """Flow: collect inputs and add a new lead."""
    print_header("Add New Lead")
    name   = input_nonempty("Name: ")
    phone  = input_optional("Phone (optional): ")
    source = input_optional("Source (optional, e.g. Facebook, Referral, Website): ")
    notes  = input_optional("Notes (optional): ")

    try:
        new_id = leads.add_lead(name, phone, source, notes)
        print_success(f"Lead added successfully! ID: {new_id}")
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_view_leads() -> None:
    """Flow: display all leads in a table."""
    print_header("All Leads")
    rows = leads.get_all_leads()
    print_table(
        rows,
        columns=["id", "name", "phone", "source", "status", "notes"],
        headers=["ID", "Name", "Phone", "Source", "Status", "Notes"],
    )
    pause()


def _flow_update_lead_status() -> None:
    """Flow: show leads table, then update the status of a chosen lead."""
    print_header("Update Lead Status")
    rows = leads.get_all_leads()
    print_table(
        rows,
        columns=["id", "name", "phone", "source", "status"],
        headers=["ID", "Name", "Phone", "Source", "Status"],
    )
    if not rows:
        pause()
        return

    lead_id = input_int("Enter lead ID to update: ")
    new_status = input_status("Select new status: ", leads.LEAD_STATUS_OPTIONS)

    try:
        found = leads.update_lead_status(lead_id, new_status)
        if found:
            print_success(f"Lead #{lead_id} status updated to \"{new_status}\".")
        else:
            print_error(f"No lead found with ID {lead_id}.")
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_convert_lead() -> None:
    """Flow: show leads table, then convert a chosen lead to a customer."""
    print_header("Convert Lead to Customer")
    rows = leads.get_all_leads()
    print_table(
        rows,
        columns=["id", "name", "phone", "source", "status"],
        headers=["ID", "Name", "Phone", "Source", "Status"],
    )
    if not rows:
        pause()
        return

    lead_id = input_int("Enter lead ID to convert: ")

    try:
        new_customer_id = leads.convert_lead_to_customer(lead_id)
        print_success(
            f"Lead #{lead_id} converted to customer successfully!\n"
            f"  {c('New customer ID:', CYAN)} {new_customer_id}\n"
            f"  Lead status automatically updated to \"Converted\"."
        )
    except ValueError as e:
        print_error(str(e))

    pause()


def _flow_delete_lead() -> None:
    """Flow: show leads table, then delete a chosen lead."""
    print_header("Delete Lead")
    rows = leads.get_all_leads()
    print_table(
        rows,
        columns=["id", "name", "phone", "source", "status"],
        headers=["ID", "Name", "Phone", "Source", "Status"],
    )
    if not rows:
        pause()
        return

    lead_id = input_int("Enter lead ID to delete: ")
    if confirm(f"Are you sure you want to delete lead #{lead_id}?"):
        found = leads.delete_lead(lead_id)
        if found:
            print_success(f"Lead #{lead_id} deleted successfully.")
        else:
            print_error(f"No lead found with ID {lead_id}.")
    else:
        print(c("  Deletion cancelled.", DIM))

    pause()


def menu_leads() -> None:
    """Leads sub-menu loop."""
    while True:
        clear_screen()
        print_box_menu("Manage Leads", [
            "  1.  Add New Lead",
            "  2.  View All Leads",
            "  3.  Update Lead Status",
            "  4.  Convert Lead to Customer",
            "  5.  Delete Lead",
            "  0.  Back to Main Menu",
        ])
        choice = input(c("\n  Select an option: ", YELLOW)).strip()

        if choice == "1":
            clear_screen()
            _flow_add_lead()
        elif choice == "2":
            clear_screen()
            _flow_view_leads()
        elif choice == "3":
            clear_screen()
            _flow_update_lead_status()
        elif choice == "4":
            clear_screen()
            _flow_convert_lead()
        elif choice == "5":
            clear_screen()
            _flow_delete_lead()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice. Please enter a number from the menu.")
            pause()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Business Info Screen
# ─────────────────────────────────────────────────────────────────────────────

def _show_business_info(business: Business) -> None:
    """Display business details (name, owner, working hours, services)."""
    print_header("Business Information")
    print(f"  {c('Business Name:', CYAN)} {c(business.name, BOLD + WHITE)}")
    if business.owner:
        print(f"  {c('Owner:        ', CYAN)} {business.owner}")
    start_h = business.working_hours.get("start", "N/A")
    end_h = business.working_hours.get("end", "N/A")
    print(f"  {c('Working Hours:', CYAN)} {start_h} – {end_h}")
    print(f"  {c('Services:     ', CYAN)} {business.services_display()}")
    pause()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Statistics & Reports
# ─────────────────────────────────────────────────────────────────────────────

def show_dashboard(business: Business) -> None:
    """
    Display a startup statistics dashboard with headline numbers.
    Called from menu_main before the menu loop, so the user sees it right away.
    """
    data = stats.get_dashboard_stats()
    width = 46
    border  = c("═" * width, CYAN)
    print(f"\n{border}")
    print(c(f"  {'DASHBOARD — ' + business.name}", CYAN + BOLD))
    print(f"{border}")

    # Appointments block
    print(c(f"  Appointments", CYAN))
    print(f"    Total:      {data['total_appointments']}")
    print(f"    {c('Pending:  ', YELLOW)}  {data['pending']}")
    print(f"    {c('Completed:', GREEN)}  {data['completed']}")
    print(f"    {c('Cancelled:', RED)}  {data['cancelled']}")
    if data['todays_count'] > 0:
        print(c(f"    ★ Today:    {data['todays_count']} appointment(s) scheduled today", YELLOW + BOLD))
    else:
        print(c(f"    Today:      No appointments scheduled today.", DIM))

    print()
    # Business block
    print(c(f"  Business", CYAN))
    print(f"    Customers:  {data['total_customers']}")
    print(f"    Leads:      {data['total_leads']}")
    print(f"    Revenue:    {data['total_revenue']:.0f} ILS")
    if data['top_service']:
        print(f"    Top service: {data['top_service']}")

    print(f"{border}\n")


def _flow_revenue_by_customer() -> None:
    """Flow: show revenue totals per customer."""
    print_header("Revenue by Customer")
    rows = stats.get_revenue_by_customer()
    print_table(
        rows,
        columns=["name", "total_revenue", "invoice_count"],
        headers=["Customer", "Revenue (ILS)", "# Invoices"],
    )
    pause()


def _flow_revenue_by_service() -> None:
    """Flow: show appointment counts and completion rate per service."""
    print_header("Appointments by Service Type")
    rows = stats.get_revenue_by_service()
    print_table(
        rows,
        columns=["service_type", "appointment_count", "completed_count", "cancelled_count"],
        headers=["Service", "Total", "Completed", "Cancelled"],
    )
    pause()


def _flow_revenue_by_month() -> None:
    """Flow: show invoiced revenue per calendar month."""
    print_header("Revenue by Month")
    rows = stats.get_revenue_by_month()
    if not rows:
        print(c("\n  No invoice data yet.", DIM))
    else:
        print_table(
            rows,
            columns=["month_label", "total_revenue", "invoice_count"],
            headers=["Month", "Revenue (ILS)", "# Invoices"],
        )
    pause()


def menu_stats() -> None:
    """Statistics & Reports sub-menu loop."""
    while True:
        clear_screen()
        print_box_menu("Statistics & Reports", [
            "  1.  Revenue by Customer",
            "  2.  Appointments by Service Type",
            "  3.  Revenue by Month",
            "  0.  Back to Main Menu",
        ])
        choice = input(c("\n  Select an option: ", YELLOW)).strip()

        if choice == "1":
            clear_screen()
            _flow_revenue_by_customer()
        elif choice == "2":
            clear_screen()
            _flow_revenue_by_service()
        elif choice == "3":
            clear_screen()
            _flow_revenue_by_month()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice. Please enter a number from the menu.")
            pause()


# ─────────────────────────────────────────────────────────────────────────────
# 9. Main Menu (entry point)
# ─────────────────────────────────────────────────────────────────────────────

def menu_main(business: Business) -> None:
    """
    Top-level main menu loop.
    Called from main.py after the database has been initialized.

    Args:
        business: The configured Business instance (created in main.py).
    """
    while True:
        clear_screen()
        # Show dashboard stats above the menu on every loop
        show_dashboard(business)
        print_box_menu(f"{business.name}  —  Appointment Manager", [
            "  1.  Manage Appointments",
            "  2.  Manage Customers & Invoices",
            "  3.  Manage Leads",
            "  4.  Statistics & Reports",
            "  5.  Business Info",
            "  0.  Exit",
        ])
        choice = input(c("\n  Select an option: ", YELLOW)).strip()

        if choice == "1":
            menu_appointments(business)
        elif choice == "2":
            menu_customers()
        elif choice == "3":
            menu_leads()
        elif choice == "4":
            menu_stats()
        elif choice == "5":
            clear_screen()
            _show_business_info(business)
        elif choice == "0":
            clear_screen()
            width = 44
            border = c("╔" + "═" * width + "╗", CYAN)
            print(f"\n{border}")
            print(c(f"║{'Thank you for using'.center(width)}║", CYAN))
            print(c(f"║{(business.name + ' Appointment Manager').center(width)}║", CYAN + BOLD))
            print(c(f"║{''.center(width)}║", CYAN))
            print(c(f"║{'Goodbye! 👋'.center(width)}║", CYAN))
            print(c("╚" + "═" * width + "╝", CYAN))
            print()
            break
        else:
            print_error("Invalid choice. Please enter a number from the menu.")
            pause()
