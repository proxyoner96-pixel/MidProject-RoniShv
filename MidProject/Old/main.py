"""
main.py
=======
קובץ ההרצה הראשי של המערכת. זהו הקובץ היחיד שמכיל אינטראקציה ישירה עם
המשתמש (input/print) - כל שאר הקבצים (appointments.py, customers.py,
leads.py, database.py) מכילים אך ורק לוגיקה עסקית וגישה לבסיס הנתונים,
בלי תלות בממשק המשתמש. הפרדה זו היא בדיוק מה שהמסמך מבקש תחת "הקוד יהיה
מאורגן במספר קבצים לפי אחריות (קובץ ראשי, קובץ גישה לבסיס הנתונים...)".

הרצה:  python main.py
"""

from database import init_db
import appointments
import customers
import leads
from utils import input_nonempty, input_date, input_time, print_table


# ---------------------------------------------------------------------------
# תפריט 1: ניהול תורים (דרישת ליבה - חובה)
# ---------------------------------------------------------------------------

def menu_appointments():
    while True:
        print("\n===== ניהול תורים =====")
        print("1. הוספת תור חדש")
        print("2. הצגת כל התורים")
        print("3. עדכון סטטוס תור")
        print("4. מחיקת תור")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר/י פעולה: ").strip()

        if choice == "1":
            add_appointment_flow()
        elif choice == "2":
            show_appointments()
        elif choice == "3":
            update_appointment_status_flow()
        elif choice == "4":
            delete_appointment_flow()
        elif choice == "0":
            break
        else:
            print("בחירה לא תקינה, נסה/י שוב.")


def add_appointment_flow():
    print("\n--- הוספת תור חדש ---")
    name = input_nonempty("שם לקוח: ")
    service = input_nonempty("סוג שירות: ")
    date = input_date("תאריך (DD/MM/YYYY): ")
    time = input_time("שעה (HH:MM): ")

    # בדיקת התנגשויות בסיסית לפני ההוספה בפועל (הבונוס המוזכר במסמך)
    conflicts = appointments.check_conflict(date, time)
    if conflicts:
        print(
            f"שים/י לב! כבר קיים תור פעיל בתאריך {date} בשעה {time} "
            f"(לקוח קיים: {conflicts[0]['customer_name']})."
        )
        confirm = input("להמשיך ולהוסיף את התור בכל זאת? (כ/ל): ").strip()
        if confirm != "כ":
            print("הוספת התור בוטלה.")
            return

    try:
        new_id = appointments.add_appointment(name, service, date, time)
        print(f"התור נוסף בהצלחה! מזהה תור: {new_id}")
    except ValueError as e:
        print(f"שגיאה: {e}")


def show_appointments():
    print("\n--- כל התורים ---")
    rows = appointments.get_all_appointments()
    print_table(
        rows,
        ["id", "customer_name", "service_type", "appointment_date", "appointment_time", "status"],
    )


def update_appointment_status_flow():
    show_appointments()
    appt_id = input("\nהזן/י מזהה תור לעדכון סטטוס: ").strip()
    if not appt_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return

    print(f"סטטוסים אפשריים: {', '.join(appointments.STATUS_OPTIONS)}")
    new_status = input("סטטוס חדש: ").strip()
    try:
        success = appointments.update_status(int(appt_id), new_status)
        print("הסטטוס עודכן בהצלחה!" if success else "לא נמצא תור עם מזהה זה.")
    except ValueError as e:
        print(f"שגיאה: {e}")


def delete_appointment_flow():
    show_appointments()
    appt_id = input("\nהזן/י מזהה תור למחיקה: ").strip()
    if not appt_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    success = appointments.delete_appointment(int(appt_id))
    print("התור נמחק בהצלחה!" if success else "לא נמצא תור עם מזהה זה.")


# ---------------------------------------------------------------------------
# תפריט 2: ניהול לקוחות וחשבוניות (בונוס 1)
# ---------------------------------------------------------------------------

def menu_customers():
    while True:
        print("\n===== ניהול לקוחות וחשבוניות מס (בונוס 1) =====")
        print("1. הוספת לקוח חדש")
        print("2. הצגת כל הלקוחות")
        print("3. מחיקת לקוח")
        print("4. יצירת חשבונית מס עבור לקוח")
        print("5. צפייה בהיסטוריית תורים וחשבוניות של לקוח")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר/י פעולה: ").strip()

        if choice == "1":
            add_customer_flow()
        elif choice == "2":
            show_customers()
        elif choice == "3":
            delete_customer_flow()
        elif choice == "4":
            create_invoice_flow()
        elif choice == "5":
            show_customer_history_flow()
        elif choice == "0":
            break
        else:
            print("בחירה לא תקינה, נסה/י שוב.")


def add_customer_flow():
    print("\n--- הוספת לקוח חדש ---")
    name = input_nonempty("שם לקוח: ")
    phone = input("טלפון (אופציונלי): ").strip()
    email = input("אימייל (אופציונלי): ").strip()
    address = input("כתובת (אופציונלי): ").strip()
    try:
        new_id = customers.add_customer(name, phone, email, address)
        print(f"הלקוח נוסף בהצלחה! מזהה לקוח: {new_id}")
    except ValueError as e:
        print(f"שגיאה: {e}")


def show_customers():
    print("\n--- כל הלקוחות ---")
    rows = customers.get_all_customers()
    print_table(rows, ["id", "name", "phone", "email", "address"])


def delete_customer_flow():
    show_customers()
    cust_id = input("\nהזן/י מזהה לקוח למחיקה: ").strip()
    if not cust_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    success = customers.delete_customer(int(cust_id))
    print("הלקוח נמחק בהצלחה!" if success else "לא נמצא לקוח עם מזהה זה.")


def create_invoice_flow():
    show_customers()
    cust_id = input("\nהזן/י מזהה לקוח ליצירת חשבונית: ").strip()
    if not cust_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    amount_str = input("סכום החשבונית (בשקלים): ").strip()
    try:
        amount = float(amount_str)
        result = customers.create_invoice(int(cust_id), amount)
        print(f"החשבונית נוצרה בהצלחה! מספר חשבונית: {result['invoice_number']}")
    except ValueError as e:
        print(f"שגיאה: {e}")


def show_customer_history_flow():
    show_customers()
    cust_id = input("\nהזן/י מזהה לקוח לצפייה בהיסטוריה: ").strip()
    if not cust_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return

    history = customers.get_customer_history(int(cust_id))
    print("\n--- היסטוריית תורים ---")
    print_table(
        history["appointments"],
        ["id", "service_type", "appointment_date", "appointment_time", "status"],
    )
    print("\n--- היסטוריית חשבוניות ---")
    print_table(history["invoices"], ["id", "invoice_number", "amount", "invoice_date"])


# ---------------------------------------------------------------------------
# תפריט 3: ניהול לידים (בונוס 2)
# ---------------------------------------------------------------------------

def menu_leads():
    while True:
        print("\n===== ניהול לידים (בונוס 2) =====")
        print("1. הוספת ליד חדש")
        print("2. הצגת כל הלידים")
        print("3. עדכון סטטוס ליד")
        print("4. המרת ליד ללקוח")
        print("5. מחיקת ליד")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר/י פעולה: ").strip()

        if choice == "1":
            add_lead_flow()
        elif choice == "2":
            show_leads()
        elif choice == "3":
            update_lead_status_flow()
        elif choice == "4":
            convert_lead_flow()
        elif choice == "5":
            delete_lead_flow()
        elif choice == "0":
            break
        else:
            print("בחירה לא תקינה, נסה/י שוב.")


def add_lead_flow():
    print("\n--- הוספת ליד חדש ---")
    name = input_nonempty("שם: ")
    phone = input("טלפון (אופציונלי): ").strip()
    source = input("מקור פנייה (אופציונלי): ").strip()
    notes = input("הערות (אופציונלי): ").strip()
    try:
        new_id = leads.add_lead(name, phone, source, notes)
        print(f"הליד נוסף בהצלחה! מזהה ליד: {new_id}")
    except ValueError as e:
        print(f"שגיאה: {e}")


def show_leads():
    print("\n--- כל הלידים ---")
    rows = leads.get_all_leads()
    print_table(rows, ["id", "name", "phone", "source", "status", "notes"])


def update_lead_status_flow():
    show_leads()
    lead_id = input("\nהזן/י מזהה ליד לעדכון סטטוס: ").strip()
    if not lead_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    print(f"סטטוסים אפשריים: {', '.join(leads.LEAD_STATUS_OPTIONS)}")
    new_status = input("סטטוס חדש: ").strip()
    try:
        success = leads.update_lead_status(int(lead_id), new_status)
        print("הסטטוס עודכן בהצלחה!" if success else "לא נמצא ליד עם מזהה זה.")
    except ValueError as e:
        print(f"שגיאה: {e}")


def convert_lead_flow():
    show_leads()
    lead_id = input("\nהזן/י מזהה ליד להמרה ללקוח: ").strip()
    if not lead_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    try:
        new_customer_id = leads.convert_lead_to_customer(int(lead_id))
        print(f"הליד הומר ללקוח בהצלחה! מזהה לקוח חדש: {new_customer_id}")
    except ValueError as e:
        print(f"שגיאה: {e}")


def delete_lead_flow():
    show_leads()
    lead_id = input("\nהזן/י מזהה ליד למחיקה: ").strip()
    if not lead_id.isdigit():
        print("שגיאה: יש להזין מספר מזהה תקין.")
        return
    success = leads.delete_lead(int(lead_id))
    print("הליד נמחק בהצלחה!" if success else "לא נמצא ליד עם מזהה זה.")


# ---------------------------------------------------------------------------
# תפריט ראשי
# ---------------------------------------------------------------------------

def main():
    # יצירת כל הטבלאות בבסיס הנתונים אם הן עוד לא קיימות
    init_db()

    while True:
        print("\n========================================")
        print("    מערכת ניהול תורים - תפריט ראשי")
        print("========================================")
        print("1. ניהול תורים")
        print("2. ניהול לקוחות וחשבוניות (בונוס)")
        print("3. ניהול לידים (בונוס)")
        print("0. יציאה")
        choice = input("בחר/י פעולה: ").strip()

        if choice == "1":
            menu_appointments()
        elif choice == "2":
            menu_customers()
        elif choice == "3":
            menu_leads()
        elif choice == "0":
            print("להתראות!")
            break
        else:
            print("בחירה לא תקינה, נסה/י שוב.")


if __name__ == "__main__":
    main()
