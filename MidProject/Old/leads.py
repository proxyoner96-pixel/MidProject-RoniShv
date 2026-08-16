"""
leads.py
========
מימוש בונוס 2 מהמסמך: "ניהול לידים (Leads)".

כולל:
- טבלת לידים נפרדת (שם, טלפון, מקור פנייה, סטטוס, הערות) - מוגדרת ב-schema.sql.
- הוספת ליד חדש ועדכון הסטטוס שלו (חדש / בטיפול / הפך ללקוח / נדחה).
- המרת ליד ללקוח קיים במערכת: יצירת רשומת לקוח חדשה מנתוני הליד
  (באמצעות הפונקציה add_customer ממודול customers.py) ועדכון סטטוס
  הליד ל-"הפך ללקוח".
"""

from database import get_connection
from customers import add_customer

# סטטוסים חוקיים לליד, בדיוק כפי שמופיע במסמך הדרישות
LEAD_STATUS_OPTIONS = ["חדש", "בטיפול", "הפך ללקוח", "נדחה"]


def add_lead(name, phone, source, notes=""):
    """מוסיפה ליד חדש. שם הליד הוא שדה חובה; שאר השדות אופציונליים."""
    if not name:
        raise ValueError("יש להזין שם עבור הליד.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO leads (name, phone, source, status, notes) VALUES (?, ?, ?, ?, ?)",
            (name, phone, source, "חדש", notes),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_leads():
    """מחזירה את כל הלידים הרשומים במערכת, החדשים ביותר קודם."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM leads ORDER BY id DESC")
        return cursor.fetchall()
    finally:
        conn.close()


def update_lead_status(lead_id, new_status):
    """
    מעדכנת את סטטוס הליד, לאחר בדיקה שהסטטוס החדש נמצא ברשימת
    הסטטוסים המותרים בלבד (ולידציה).
    """
    if new_status not in LEAD_STATUS_OPTIONS:
        raise ValueError(f"סטטוס לא תקין. הסטטוסים המותרים הם: {', '.join(LEAD_STATUS_OPTIONS)}")

    conn = get_connection()
    try:
        cursor = conn.execute("UPDATE leads SET status = ? WHERE id = ?", (new_status, lead_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_lead(lead_id):
    """מוחקת ליד קיים לפי מזהה."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def convert_lead_to_customer(lead_id):
    """
    ממירה ליד קיים ללקוח - מימוש דרישת "אפשרות להמיר ליד ללקוח קיים
    במערכת (יצירת רשומת לקוח מנתוני הליד)":

    1. שולפת מבסיס הנתונים את פרטי הליד (שם, טלפון).
    2. יוצרת רשומת לקוח חדשה עם הנתונים האלה, דרך פונקציית add_customer
       שכבר קיימת במודול customers.py - כך נמנעת כפילות קוד ליצירת לקוח.
    3. מעדכנת את סטטוס הליד המקורי ל-"הפך ללקוח".

    מחזירה את המזהה (id) של הלקוח החדש שנוצר.
    """
    conn = get_connection()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if lead is None:
            raise ValueError("לא נמצא ליד עם מזהה זה.")
    finally:
        conn.close()

    # לליד אין שדות אימייל/כתובת, ולכן הם נשמרים ריקים בלקוח החדש
    new_customer_id = add_customer(lead["name"], lead["phone"], "", "")
    update_lead_status(lead_id, "הפך ללקוח")
    return new_customer_id
