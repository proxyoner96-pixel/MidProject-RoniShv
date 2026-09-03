# DEPLOY.md — הרצה ופריסה

מסמך זה מתאר איך להריץ את הפרויקט (מערכת ניהול תורים + צ'אטבוט אימות) מקומית,
ואיך לעדכן שרת פעיל אחרי שינוי בקוד.

## 1. הרצה מקומית

### מערכת הבסיס (CLI)
```bash
cd MidProject
python main.py
```

### הצ'אטבוט (Web)
```bash
cd Chatbot
python -m venv .venv
.venv\Scripts\activate            # Windows; מק/לינוקס: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env            # מק/לינוקס: cp .env.example .env
# ערכו את .env: הוסיפו GEMINI_API_KEY (חינמי מ-https://aistudio.google.com/apikey)

python app.py
```
פתחו בדפדפן: http://localhost:5000

## 2. פריסה לשרת חינמי — PythonAnywhere (מומלץ)

**למה PythonAnywhere ולא Render/Heroku:** הצ'אטבוט משתמש ב-SQLite (`appointments.db`)
כקובץ על הדיסק. בשירותים כמו Render, ה-Free tier מוחק את הדיסק בכל הפעלה/עדכון
מחדש (ephemeral storage) — כלומר הנתונים יימחקו. ב-PythonAnywhere חשבון ה-Free
("Beginner") שומר את הקבצים באופן קבוע, כולל בין הפעלות מחדש — מתאים בדיוק
למה שיש לנו.

### הקמה ראשונית (פעם אחת)

1. הרשמה חינמית: https://www.pythonanywhere.com
2. בלשונית **Consoles** → פתחו **Bash console** ושכפלו את הריפו:
   ```bash
   git clone https://github.com/proxyoner96-pixel/MidProject-RoniShv.git
   cd MidProject-RoniShv/Chatbot
   ```
3. יצירת סביבה וירטואלית והתקנת תלויות:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 chatbot-venv
   pip install -r requirements.txt
   ```
4. יצירת קובץ `.env` בשרת (לא דרך git — הוא לא מוגש בריפו):
   ```bash
   nano .env
   # הדביקו את התוכן מ-.env.example ומלאו GEMINI_API_KEY אמיתי, שמרו (Ctrl+O, Enter, Ctrl+X)
   ```
5. בלשונית **Web** → **Add a new web app** → **Manual configuration** → Python 3.10.
6. בקטע **Virtualenv**, הזינו את הנתיב לסביבה שיצרתם (`/home/USERNAME/.virtualenvs/chatbot-venv`).
7. ערכו את קובץ ה-**WSGI configuration file** (קישור מופיע בעמוד ה-Web) כך שיטען את
   האפליקציה שלנו:
   ```python
   import sys, os
   path = '/home/USERNAME/MidProject-RoniShv/Chatbot'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.chdir(path)

   from dotenv import load_dotenv
   load_dotenv(os.path.join(path, '.env'))

   from app import app as application
   ```
8. לחצו **Reload** בעמוד ה-Web. האתר עולה בכתובת `USERNAME.pythonanywhere.com`.

### נוהל עדכון שרת (חוזר, בכל פעם שיש קוד חדש)

זהו נוהל ה-DevOps המינימלי שהבריף דורש — לא אוטומטי (בלי CI/CD), אבל קבוע ומתועד:

```bash
# 1. בלשונית Consoles, פתחו Bash console (או "$ בהמשך" בקונסולה קיימת)
cd ~/MidProject-RoniShv
git pull                          # מושך את השינויים האחרונים מ-GitHub

cd Chatbot
workon chatbot-venv
pip install -r requirements.txt   # רק אם requirements.txt השתנה

# 2. בלשונית Web, לחצו על כפתור "Reload" הירוק ליד שם האתר
```
זהו. אין צורך בשום דבר נוסף — אין build אוטומטי, זו משיכה ידנית + הפעלה מחדש,
בדיוק כפי שהבריף מבקש, אבל בתור נוהל עקבי שכתוב פה ולא "עשיתי פעם ושכחתי".

## 3. אלטרנטיבה: Render (אם מעדיפים)

אפשר גם ב-Render Free Web Service, אך יש לצרף **Persistent Disk** (בתשלום symbolic,
או להעביר את ה-DB ל-Render Postgres החינמי) כדי שהנתונים לא יימחקו בכל redeploy.
ללא זה, `appointments.db` יאופס בכל הפעלה מחדש — לא מתאים להדגמה אמינה.

## 4. בדיקת תקינות מהירה אחרי כל פריסה

1. גלשו ל-`https://USERNAME.pythonanywhere.com/healthz` — אמור להחזיר `{"status": "ok"}`.
2. גלשו לעמוד הראשי ונסו את התרחיש המרכזי (ראו `Chatbot/TEST_SCENARIOS.md`).
