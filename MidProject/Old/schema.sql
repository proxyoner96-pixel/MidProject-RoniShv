-- schema.sql
-- ============================================================
-- קובץ הסכמה של בסיס הנתונים (Database Schema).
-- כאן מוגדרות כל הטבלאות של המערכת: התורים, הלקוחות, החשבוניות והלידים,
-- כולל מפתחות ראשיים (PRIMARY KEY) ומפתחות זרים (FOREIGN KEY) ביניהן.
-- הקובץ נטען אוטומטית ע"י database.py בפונקציה init_db() בכל הרצה של התוכנית,
-- ולכן משתמשים בביטוי IF NOT EXISTS כדי לא ליצור טבלה קיימת מחדש ולא לאבד מידע.
-- ============================================================

-- טבלת לקוחות (חלק מבונוס 1 - ניהול לקוחות)
CREATE TABLE IF NOT EXISTS customers (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    phone   TEXT,
    email   TEXT,
    address TEXT
);

-- טבלת התורים - הליבה של הפרויקט (דרישה חובה)
-- customer_id הוא מפתח זר אופציונלי לטבלת customers (תור יכול להיות מקושר ללקוח קיים,
-- אך גם יכול להישמר רק עם שם לקוח חופשי, כפי שנדרש בדרישות הליבה).
CREATE TABLE IF NOT EXISTS appointments (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id       INTEGER,
    customer_name     TEXT NOT NULL,
    service_type      TEXT NOT NULL,
    appointment_date  TEXT NOT NULL,   -- פורמט DD/MM/YYYY
    appointment_time  TEXT NOT NULL,   -- פורמט HH:MM
    status            TEXT NOT NULL DEFAULT 'ממתין',  -- ממתין / בוצע / בוטל
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL
);

-- טבלת חשבוניות מס (חלק מבונוס 1)
-- מחיקת לקוח תמחק אוטומטית גם את החשבוניות שלו (ON DELETE CASCADE)
CREATE TABLE IF NOT EXISTS invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    invoice_number  TEXT UNIQUE NOT NULL,
    amount          REAL NOT NULL,
    invoice_date    TEXT NOT NULL,     -- פורמט DD/MM/YYYY
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

-- טבלת לידים (בונוס 2 - ניהול לידים)
CREATE TABLE IF NOT EXISTS leads (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    phone   TEXT,
    source  TEXT,                                  -- מקור הפנייה (פייסבוק, המלצה וכו')
    status  TEXT NOT NULL DEFAULT 'חדש',            -- חדש / בטיפול / הפך ללקוח / נדחה
    notes   TEXT
);
