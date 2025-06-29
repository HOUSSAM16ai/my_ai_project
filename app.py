from flask import Flask

app = Flask(__name__)

import os
from flask import Flask
import psycopg2
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (سننشئه لاحقًا)
load_dotenv()

app = Flask(__name__)

def get_db_connection():
    """
    دالة للاتصال بقاعدة البيانات.
    تقوم بقراءة معلومات الاتصال من متغيرات البيئة.
    """
    try:
        conn = psycopg2.connect(
            host="db", # اسم خدمة قاعدة البيانات كما سنعرفه في docker-compose.yml
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        return conn
    except psycopg2.OperationalError as e:
        # في حالة فشل الاتصال، نرجع None ونطبع الخطأ
        print(f"Could not connect to the database: {e}")
        return None

@app.route('/')
def hello():
    conn = get_db_connection()
    if conn:
        # إذا نجح الاتصال، أغلقه وأرجع رسالة نجاح
        conn.close()
        return "Successfully connected to the PostgreSQL database!"
    else:
        # إذا فشل الاتصال، أرجع رسالة فشل
        return "Could not connect to the database. Please check the logs."

# لا حاجة لـ app.run() هنا لأن Gunicorn سيتولى التشغيل
