# ai_service/main.py - The All-Knowing AI Oracle v5.2 (Code Generation Enabled)

import os
from contextlib import asynccontextmanager

import openai
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException
from pydantic import BaseModel

# We need these for the restored database routes
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- [AI Oracle Lifespan] System Awakening...")
    load_dotenv()
    # --- Database Connection ---
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_HOST = os.getenv("POSTGRES_HOST", "db")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        app.state.db_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ [AI Oracle] Database connection pool forged.")
    except Exception as e:
        print(f"❌ [AI Oracle] FATAL: Could not connect to database: {e}")
        app.state.db_session_factory = None
    # --- AI Client Connection ---
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("⚠️ [AI Oracle] WARNING: OPENROUTER_API_KEY is not set.")
            app.state.ai_client = None
        else:
            app.state.ai_client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1", api_key=api_key
            )
            print("✅ [AI Oracle] OpenRouter client configured.")
    except Exception as e:
        print(f"❌ [AI Oracle] FATAL: Error configuring AI client: {e}")
        app.state.ai_client = None
    yield
    print("--- [AI Oracle Lifespan] System entering graceful shutdown...")


app = FastAPI(lifespan=lifespan, title="CogniForge AI Oracle & System Services", version="5.2.0")


# --- Dependency Injection System ---
def get_db():
    if not app.state.db_session_factory:
        raise HTTPException(status_code=503, detail="Database service is unavailable.")
    db = app.state.db_session_factory()
    try:
        yield db
    finally:
        db.close()


def get_ai_client():
    if not app.state.ai_client:
        raise HTTPException(status_code=503, detail="AI Service is not configured.")
    return app.state.ai_client


# --- Data Models for Payloads ---
class GenerateCodePayload(BaseModel):
    prompt: str
    context: str


# --- Core & AI Endpoints ---


@app.get("/", tags=["System Status"])
def read_root():
    return {"status": "AI Oracle Online"}


@app.post("/ai/chat/completion", tags=["AI Features"])
async def chat_completion(
    payload: dict = Body(...), client: openai.OpenAI = Depends(get_ai_client)
):
    try:
        model = payload.get("model", "mistralai/mistral-7b-instruct")
        messages = payload.get("messages", [])
        completion = client.chat.completions.create(model=model, messages=messages)
        return {"status": "success", "data": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- [THE ULTIMATE ADDITION] The Context-Aware Creation Endpoint ---
@app.post("/ai/generate/code", tags=["AI Features"])
async def generate_code_with_context(
    payload: GenerateCodePayload = Body(...), client: openai.OpenAI = Depends(get_ai_client)
):
    """
    Receives a prompt and code context, then generates new, complete code.
    This is the core of the system's creative power.
    """
    system_prompt = f"""
    You are an expert Flask and Python developer. Your task is to generate clean,
    efficient, and complete Python code based on a user's prompt and relevant
    code context provided from the existing codebase.

    **User's Request:**
    {payload.prompt}

    **Relevant Code Context from the project:**
    ---
    {payload.context}
    ---

    Based on the request and the context, provide the complete, ready-to-use
    Python code for the new feature or modification. Only output the raw code,
    without any explanations, comments, or markdown formatting like ```python or ```.
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o",  # Using a powerful model for code generation
            messages=[
                {"role": "system", "content": "You are a world-class code generation engine."},
                {"role": "user", "content": system_prompt},
            ],
            temperature=0.2,  # Low temperature for precise and deterministic code
            max_tokens=4000,  # Generous token limit for larger files
        )
        generated_code = completion.choices[0].message.content
        return {"status": "success", "generated_code": generated_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Diagnostic and Admin Routes ---


@app.get("/diagnostics/ai-connection", tags=["Diagnostics"])
def test_ai_connection(client: openai.OpenAI = Depends(get_ai_client)):
    """Performs a LIVE test of the connection to the AI model provider."""
    try:
        models = client.models.list()
        return {
            "status": "success",
            "message": f"Successfully connected. {len(models.data)} models available.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/admin/vitals/user-count", tags=["Admin Vitals"])
async def get_user_count(db: Session = Depends(get_db)):
    """Directly queries the database for the total number of users."""
    try:
        user_count = db.execute(text("SELECT COUNT(id) FROM public.user")).scalar_one()
        return {"status": "success", "data": user_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@app.get("/admin/vitals/users", tags=["Admin Vitals"])
async def list_all_users(db: Session = Depends(get_db)):
    """Directly queries and returns a list of all users."""
    try:
        users_query = db.execute(text("SELECT id, full_name, email FROM public.user ORDER BY id"))
        users = [dict(row) for row in users_query.mappings().all()]
        return {"status": "success", "data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
