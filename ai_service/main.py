# ai_service/main.py - Supercharged with Database Connection Testing

import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (مفيد للاختبار المحلي)
load_dotenv()

# --- إعدادات الاتصال بقاعدة البيانات ---
# قراءة متغيرات البيئة التي تم تمريرها من docker-compose.yml
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "db") # القيمة الافتراضية هي 'db'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# محاولة إنشاء محرك قاعدة البيانات عند بدء التشغيل
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Database engine created and connection pool configured.")
except Exception as e:
    print(f"❌ FATAL: Error creating database engine: {e}")
    engine = None
    SessionLocal = None

# --- تطبيق FastAPI ---
app = FastAPI(
    title="CogniForge AI Service",
    description="The intelligent core for analyzing and understanding user interactions.",
    version="0.1.0",
)

# --- دالة مساعدة للحصول على جلسة قاعدة بيانات (Dependency) ---
def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="Database session is not available.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- نقاط النهاية (Endpoints) ---
@app.get("/")
def read_root():
    """Returns a welcome message."""
    return {"message": "CogniForge AI Analysis Service is running!"}

@app.get("/test-db-connection", tags=["Database"])
def test_db_connection(db: Session = Depends(get_db)):
    """
    Tests the connection to the database by fetching the server version.
    This is a simple, non-intrusive health check.
    """
    try:
        # تنفيذ استعلام بسيط جدًا للتأكد من أن الاتصال يعمل
        result = db.execute(text("SELECT version()")).scalar_one_or_none()
        if result:
            return {"status": "success", "db_version": result}
        else:
            raise HTTPException(status_code=500, detail="Query executed but no result was returned.")
            
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/subjects-count", tags=["Database"])
def get_subjects_count(db: Session = Depends(get_db)):
    """
    Fetches the total number of subjects from the database to test table access.
    """
    try:
        # استعلام لعد المواد الموجودة في جدول subjects
        count = db.execute(text("SELECT COUNT(id) FROM subjects")).scalar_one()
        return {"status": "success", "subjects_count": count}
    except Exception as e:
        # إذا فشل، فهذا يعني أن الجدول غير موجود أو هناك مشكلة أخرى
        raise HTTPException(status_code=500, detail=f"Could not query subjects table: {e}")