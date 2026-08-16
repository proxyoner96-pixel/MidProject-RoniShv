"""
customers.py
============
מימוש בונוס 1 מהמסמך: "ניהול לקוחות וחשבוניות מס".

כולל:
- טבלת לקוחות נפרדת (שם, טלפון, אימייל, כתובת) - מוגדרת ב-schema.sql.
- הוספה, צפייה ומחיקה של לקוחות.
- קישור בין תור ללקוח קיים - נעשה בפועל דרך השדה customer_id בטבלת
  appointments (מפתח זר), שנוצר ומטופל במודול appointments.py.
- יצירת חשבונית מס עבור לקוח, עם מספר חשבונית ייחודי, סכום ותאריך.
- צפייה בהיסטוריית תורים וחשבוניות עבור כל לקוח (get_customer_history).
"""

from datetime import date as date_module
from database import get_connection


def add_customer(name, phone, email, address):
    """
    מוסיפה לקוח חדש לבסיס הנתונים ומחזירה את המזהה שלו.
    שם הלקוח הוא שדה חובה (ולידציה בסיסית); שאר השדות אופציונליים,
    בדיוק כפי שמוגדר במסמך הדרישות (שם, טלפון, אימייל, כתובת).
    """
    if not name:
        raise ValueError("יש להזין שם לקוח.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (name, phone, email, address),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_customers():
    """מחזירה את כל הלקוחות הרשומים במערכת, ממוינים לפי שם."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM customers ORDER BY name")
        return cursor.fetchall()
    finally:
        conn.close()


def get_customer(customer_id):
    """מחזירה לקוח בודד לפי מזהה, או None אם לא קיים."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def delete_customer(customer_id):
    """
    מוחקת לקוח לפי מזהה.
    בזכות ON DELETE CASCADE שהוגדר על טבלת invoices ב-schema.sql, מחיקת לקוח
    תמחק אוטומטית גם את כל החשבוניות שלו. לעומת זאת, בטבלת appointments
    הוגדר ON DELETE SET NULL - כלומר תורים קיימים של הלקוח לא יימחקו,
    אלא רק "ינותקו" ממנו (customer_id יהפוך ל-NULL, ושם הלקוח החופשי
    שכבר נשמר בתור עצמו יישאר).
    """
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def _generate_invoice_number(conn):
    """
    פונקציית עזר פנימית (מסומנת ב-'_' כדי לציין שהיא לשימוש פנימי במודול בלבד)
    שיוצרת מספר חשבונית ייחודי בפורמט INV-0001, INV-0002 וכן הלאה, לפי מספר
    החשבוניות שכבר קיימות בבסיס הנתונים + 1.
    """
    cursor = conn.execute("SELECT COUNT(*) AS count FROM invoices")
    count = cursor.fetchone()["count"]
    return f"INV-{count + 1:04d}"


def create_invoice(customer_id, amount, invoice_date=None):
    """
    יוצרת חשבונית מס עבור לקוח קיים - מימוש דרישת "יצירת חשבונית מס עבור
    לקוח, הכוללת מספר חשבונית ייחודי, סכום ותאריך".

    amount       - סכום החשבונית; חייב להיות מספר חיובי (ולידציה).
    invoice_date - תאריך בפורמט DD/MM/YYYY; אם לא סופק, נלקח תאריך היום
                   באופן אוטומטי.
    מחזירה dict עם המזהה החדש ומספר החשבונית שנוצר.
    """
    if amount is None or amount <= 0:
        raise ValueError("סכום החשבונית חייב להיות מספר חיובי.")

    if invoice_date is None:
        invoice_date = date_module.today().strftime("%d/%m/%Y")

    conn = get_connection()
    try:
        customer = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        if customer is None:
            raise ValueError("לא נמצא לקוח עם מזהה זה.")

        invoice_number = _generate_invoice_number(conn)
        cursor = conn.execute(
            """INSERT INTO invoices (customer_id, invoice_number, amount, invoice_date)
               VALUES (?, ?, ?, ?)""",
            (customer_id, invoice_number, amount, invoice_date),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "invoice_number": invoice_number}
    finally:
        conn.close()


def get_customer_history(customer_id):
    """
    מחזירה dict עם שני מפתחות - "appointments" ו-"invoices" - המכילים את
    כל התורים וכל החשבוניות ששייכים ללקוח הנתון.
    זהו המימוש של דרישת "צפייה בהיסטוריית תורים וחשבוניות עבור כל לקוח".
    """
    conn = get_connection()
    try:
        appointments_rows = conn.execute(
            "SELECT * FROM appointments WHERE customer_id = ? ORDER BY appointment_date",
            (customer_id,),
        ).fetchall()
        invoices_rows = conn.execute(
            "SELECT * FROM invoices WHERE customer_id = ? ORDER BY invoice_date",
            (customer_id,),
        ).fetchall()
        return {"appointments": appointments_rows, "invoices": invoices_rows}
    finally:
        conn.close()
