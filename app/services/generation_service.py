# app/services/generation_service.py - The Central Logic Ministry

import openai
import chromadb
from sentence_transformers import SentenceTransformer
from flask import current_app

# --- تحميل نموذج الفهم مسبقًا ليكون جاهزًا دائمًا ---
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ [Generation Service] Embedding model loaded successfully.")
except Exception as e:
    embedding_model = None
    print(f"⚠️ [Generation Service] WARNING: Could not preload embedding model: {e}")

def get_model():
    """ يضمن أن النموذج متاح، ويقوم بتحميله عند الطلب إذا فشل التحميل المسبق. """
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model

def forge_new_code(prompt: str) -> dict:
    """
    هذه هي الدالة الأساسية والوحيدة للخلق. إنها "مصدر الحقيقة" للنظام.
    تتلقى طلبًا وتعيد قاموسًا يحتوي على الكود أو الخطأ.
    """
    try:
        # --- الخطوة 1: جلب السياق من الذاكرة ---
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        model = get_model()
        query_embedding = model.encode([prompt])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=5
        )
        context = "\n---\n".join(results['documents'][0])
        sources = [meta['source'] for meta in results['metadatas'][0]]

        # --- الخطوة 2: الاتصال المباشر بالذكاء الاصطناعي ---
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            return {"error": "CRITICAL: OPENROUTER_API_KEY is not configured."}

        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=90.0,
        )
        
        system_prompt = f"""
        You are an expert Flask and Python developer. Your task is to generate clean,
        efficient, and complete Python code based on a user's prompt and relevant
        code context provided from the existing codebase.

        **User's Request:**
        {prompt}

        **Relevant Code Context from the project:**
        ---
        {context}
        ---

        Based on the request and the context, provide the complete, ready-to-use
        Python code for the new feature or modification. Only output the raw code,
        without any explanations, comments, or markdown formatting like ```python or ```.
        """
        
        completion = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You are a world-class code generation engine."},
                {"role": "user", "content": system_prompt},
            ],
            temperature=0.2
        )
        generated_code = completion.choices[0].message.content
        
        return {"status": "success", "code": generated_code, "sources": sources}

    except Exception as e:
        return {"status": "error", "message": str(e)}