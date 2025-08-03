# ai_service/main.py - v0.2 (AI Integration and Drawing Analysis Endpoint)

import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import openai # <-- 1. استيراد مكتبة OpenAI (التي تعمل مع OpenRouter)

# --- تحميل متغيرات البيئة ---
load_dotenv()

# --- إعدادات قاعدة البيانات ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Database engine created.")
except Exception as e:
    print(f"❌ FATAL: Error creating database engine: {e}")
    engine = None; SessionLocal = None

# --- إعدادات OpenRouter AI ---
# 2. قراءة مفتاح API وتكوين العميل
try:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        print("⚠️ WARNING: OPENROUTER_API_KEY is not set. AI features will be disabled.")
        ai_client = None
    else:
        ai_client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        print("✅ OpenRouter AI client configured successfully.")
except Exception as e:
    print(f"❌ FATAL: Error configuring AI client: {e}")
    ai_client = None

# --- تطبيق FastAPI ---
app = FastAPI(
    title="CogniForge AI Service",
    version="0.2.0",
)

# --- دالة مساعدة للحصول على جلسة قاعدة بيانات ---
def get_db():
    if SessionLocal is None: raise HTTPException(status_code=500, detail="Database not available.")
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- نقاط النهاية (Endpoints) ---
@app.get("/")
def read_root():
    return {"message": "CogniForge AI Analysis Service is running!"}

# --- 4. نقطة نهاية جديدة لاختبار الـ AI ---
@app.get("/test-ai-connection", tags=["AI"])
def test_ai_connection():
    """Tests connection to the AI model provider by asking a simple question."""
    if ai_client is None:
        raise HTTPException(status_code=503, detail="AI Service is not configured.")
    try:
        completion = ai_client.chat.completions.create(
            model="google/gemini-pro",
            messages=[
                {"role": "user", "content": "What is the capital of Algeria?"},
            ],
        )
        return {"status": "success", "response": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI provider error: {str(e)}")

# --- 5. نقطة النهاية الرئيسية للميزة الجديدة ---
@app.post("/analyze-drawing", tags=["AI Analysis"])
async def analyze_drawing(image: UploadFile = File(...)):
    """
    Receives an image of a drawing for future analysis.
    (This is a placeholder for now).
    """
    if not image:
        raise HTTPException(status_code=400, detail="No image file provided.")
    
    # في المستقبل: هنا ستقوم باستدعاء OpenCV و ai_client لتحليل الصورة
    
    return {
        "filename": image.filename,
        "content_type": image.content_type,
        "status": "Image received successfully, ready for future analysis."
    }

# --- نقاط النهاية القديمة للاختبار (يمكن إبقاؤها) ---
@app.get("/test-db-connection", tags=["Database"])
def test_db_connection(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT version()")).scalar_one_or_none()
    return {"status": "success", "db_version": result}

@app.get("/subjects-count", tags=["Database"])
def get_subjects_count(db: Session = Depends(get_db)):
    count = db.execute(text("SELECT COUNT(id) FROM subjects")).scalar_one()
    return {"status": "success", "subjects_count": count}