"""
appointments.py
================
זהו המודול המרכזי של הפרויקט - מימוש דרישות הליבה (חובה) מהמסמך:
הוספת תור, הצגת כל התורים, עדכון סטטוס תור, מחיקת תור, ובנוסף בדיקת
התנגשויות בסיסית (שמוגדרת במסמך כ"יתרון, לא חובה" ומומשה כאן במלואה).

כל פונקציה פותחת חיבור לבסיס הנתונים באמצעות database.get_connection(),
ותמיד סוגרת אותו בסוף בבלוק finally - כך שהחיבור ייסגר גם אם מתרחשת שגיאה
באמצע הפעולה, ולא "נזלוג" חיבורים פתוחים במערכת.
"""

from database import get_connection

# סטטוסים חוקיים לתור - משמש גם לוולידציה וגם להצגה למשתמש בתפריט
STATUS_OPTIONS = ["ממתין", "בוצע", "בוטל"]


def check_conflict(date, time):
    """
    בודקת אם כבר קיים תור *פעיל* (סטטוס שונה מ"בוטל") באותו תאריך ובאותה שעה.
    מחזירה רשימת שורות מתנגשות (יכולה להיות ריקה אם אין התנגשות).

    זהו המימוש של "מניעת התנגשויות בסיסית" מהמסמך - נקראת ע"י main.py
    *לפני* הוספת תור חדש, כדי להתריע למשתמש ולתת לו לבחור אם להמשיך.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """SELECT * FROM appointments
               WHERE appointment_date = ? AND appointment_time = ? AND status != 'בוטל'""",
            (date, time),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def add_appointment(customer_name, service_type, date, time, customer_id=None):
    """
    מוסיפה תור חדש לבסיס הנתונים ומחזירה את המזהה (id) שנוצר לו.

    טיפול בשגיאות: אם אחד השדות החיוניים (שם לקוח / סוג שירות / תאריך / שעה)
    ריק, נזרקת ValueError עם הודעה ברורה. כך מיושמת דרישת המסמך המפורשת:
    "לא לאפשר הוספת תור ללא תאריך" (וכנ"ל לגבי שאר השדות).
    customer_id הוא אופציונלי - מאפשר (בבונוס 1) לקשר את התור ללקוח קיים
    בטבלת customers, אך אינו חובה כדי לענות על דרישת הליבה הבסיסית.
    """
    if not customer_name or not service_type or not date or not time:
        raise ValueError("יש למלא שם לקוח, סוג שירות, תאריך ושעה - כל השדות הם חובה.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO appointments
               (customer_id, customer_name, service_type, appointment_date, appointment_time, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, customer_name, service_type, date, time, "ממתין"),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_appointments():
    """
    מחזירה את כל התורים הקיימים במערכת, ממוינים לפי תאריך ואז שעה -
    מימוש דרישת "הצגת רשימת כל התורים הקיימים במערכת".
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM appointments ORDER BY appointment_date, appointment_time"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_appointment(appointment_id):
    """מחזירה שורת תור בודדת לפי מזהה, או None אם לא נמצא תור כזה."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def update_status(appointment_id, new_status):
    """
    מעדכנת את סטטוס התור הנתון (ממתין / בוצע / בוטל) -
    מימוש דרישת "עדכון סטטוס תור".
    מבצעת ולידציה שהסטטוס שנשלח נמצא ברשימת הסטטוסים החוקיים בלבד.
    מחזירה True אם התור נמצא ועודכן, ו-False אם לא נמצא תור עם מזהה כזה.
    """
    if new_status not in STATUS_OPTIONS:
        raise ValueError(f"סטטוס לא תקין. הסטטוסים המותרים הם: {', '.join(STATUS_OPTIONS)}")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE appointments SET status = ? WHERE id = ?", (new_status, appointment_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_appointment(appointment_id):
    """
    מוחקת תור קיים לפי מזהה - מימוש דרישת "מחיקת תור קיים".
    מחזירה True אם אכן נמחקה שורה, ו-False אם לא נמצא תור עם מזהה זה.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
