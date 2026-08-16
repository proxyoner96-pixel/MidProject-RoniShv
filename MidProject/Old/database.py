"""
database.py
============
מודול זה אחראי אך ורק על הקשר לבסיס הנתונים SQLite: פתיחת חיבור, ואתחול
הטבלאות מתוך קובץ schema.sql. כל שאר המודולים במערכת (appointments.py,
customers.py, leads.py) פונים לפונקציית get_connection() שכאן במקום לפתוח
חיבור בעצמם - כך כל הלוגיקה של "איך מתחברים לבסיס הנתונים" מרוכזת במקום
אחד בלבד, בהתאם לדרישה במסמך הפרויקט על "מבנה קוד מודולרי" והפרדת אחריות
בין קבצים (קובץ ראשי / קובץ גישה לבסיס נתונים / וכו').
"""

import sqlite3
import os

# בסיס הנתונים וקובץ הסכמה נמצאים תמיד באותה תיקייה כמו קובץ זה,
# כך שהתוכנית תעבוד גם אם מריצים אותה מתיקיית עבודה (working directory) אחרת.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "appointments.db")
SCHEMA_PATH = os.path.join(_BASE_DIR, "schema.sql")


def get_connection():
    """
    פותחת ומחזירה חיבור (Connection) חדש לבסיס הנתונים.

    שתי נקודות חשובות כאן:
    1. conn.row_factory = sqlite3.Row - מאפשר לגשת לעמודות בתוצאה לפי שם
       (למשל row["name"]) ולא רק לפי אינדקס מספרי, מה שהופך את שאר הקוד
       לקריא הרבה יותר.
    2. PRAGMA foreign_keys = ON - חשוב במיוחד! ב-SQLite אכיפת מפתחות זרים
       (Foreign Keys) כבויה כברירת מחדל בכל חיבור חדש, ולכן חייבים להפעיל
       אותה במפורש כדי ש-ON DELETE CASCADE / ON DELETE SET NULL בקובץ
       schema.sql באמת יעבדו בפועל.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    מריצה את קובץ schema.sql על בסיס הנתונים ויוצרת את כל הטבלאות
    אם הן עדיין לא קיימות (בזכות IF NOT EXISTS בקובץ הסכמה, אפשר להריץ
    פונקציה זו בכל פעם שהתוכנית עולה בלי לפגוע בנתונים קיימים).
    נקראת פעם אחת בתחילת main.py.
    """
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
