"""
utils.py
========
פונקציות עזר כלליות שמשמשות בעיקר את main.py: תיקוף (validation) קלט של
תאריך ושעה, קבלת קלט "בטוחה" מהמשתמש (שחוזרת ושואלת עד שמתקבל קלט תקין),
והדפסת רשימות תוצאות (למשל רשימת תורים) כטבלה מסודרת במסך.

ריכוז הפונקציות האלה כאן, במקום לשכפל אותן בכל תפריט, הוא מימוש בפועל
של עקרון DRY (Don't Repeat Yourself) ותורם לאיכות הקוד ולקריאותו.
"""

from datetime import datetime

DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"


def validate_date(date_str):
    """מחזירה True אם date_str הוא תאריך תקין בפורמט DD/MM/YYYY, אחרת False."""
    try:
        datetime.strptime(date_str.strip(), DATE_FORMAT)
        return True
    except (ValueError, AttributeError):
        return False


def validate_time(time_str):
    """מחזירה True אם time_str היא שעה תקינה בפורמט HH:MM (24 שעות), אחרת False."""
    try:
        datetime.strptime(time_str.strip(), TIME_FORMAT)
        return True
    except (ValueError, AttributeError):
        return False


def input_nonempty(prompt):
    """
    מבקשת קלט טקסט מהמשתמש וחוזרת שוב ושוב עד שמתקבל קלט שאינו ריק.
    זו מימוש כללי של "טיפול בתקינות קלט" הנדרש במסמך הפרויקט.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("שגיאה: שדה זה הוא חובה ולא יכול להישאר ריק. נסה/י שוב.")


def input_date(prompt):
    """מבקשת מהמשתמש תאריך, וחוזרת ושואלת עד שמתקבל תאריך תקין."""
    while True:
        value = input(prompt).strip()
        if validate_date(value):
            return value
        print("שגיאה: תאריך לא תקין. יש להזין בפורמט DD/MM/YYYY, לדוגמה 25/12/2026.")


def input_time(prompt):
    """מבקשת מהמשתמש שעה, וחוזרת ושואלת עד שמתקבלת שעה תקינה."""
    while True:
        value = input(prompt).strip()
        if validate_time(value):
            return value
        print("שגיאה: שעה לא תקינה. יש להזין בפורמט HH:MM, לדוגמה 14:30.")


def print_table(rows, columns):
    """
    מדפיסה רשימת שורות (sqlite3.Row) כטבלת טקסט מסודרת עם יישור עמודות,
    כדי שהממשק בטרמינל יהיה קריא וברור (דרישת "ממשק משתמש תקין וברור").

    rows    - רשימת שורות (כל שורה היא sqlite3.Row, נגישה לפי מפתח כמו dict).
    columns - רשימת שמות העמודות שרוצים להציג, ובאיזה סדר.
    """
    if not rows:
        print("(אין נתונים להצגה)")
        return

    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row[col])))

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(row[col]).ljust(widths[col]) for col in columns))
