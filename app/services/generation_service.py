# app/services/generation_service.py - The Proactive Agent (v3.1)

import openai
import chromadb
import json
from flask import current_app
from . import agent_tools 
from .repo_inspector_service import get_project_summary # استيراد مباشر

def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def forge_new_code(prompt: str) -> dict:
    """
    Core function, now with the Active Memory Protocol. It ALWAYS fetches
    context first to provide the AI with a project-aware mindset.
    """
    try:
        # --- [ACTIVE MEMORY PROTOCOL] ---
        # الخطوة 1: جلب السياق من الذاكرة **أولاً وقبل كل شيء**.
        try:
            chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
            collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
            model = get_model()
            query_embedding = model.encode([prompt])
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=5 # نحصل على سياق غني
            )
            context = "\n---\n".join(results['documents'][0]) if results.get('documents') and results['documents'][0] else "No specific code context found."
            sources = [meta['source'] for meta in results['metadatas'][0]] if results.get('metadatas') and results['metadatas'][0] else []
        except Exception as e:
            context = f"Could not connect to vector memory. Error: {e}"
            sources = []
        # --- نهاية البروتوكول ---

        # الخطوة 2: تهيئة العميل
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "CRITICAL: OPENROUTER_API_KEY is not configured."}
        client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=90.0)

        # الخطوة 3: بناء "العقل العامل" للذكاء الاصطناعي
        # نحن نجمع كل المعرفة المتاحة في prompt واحد قوي.
        system_prompt = f"""
        You are CogniForge's Architect AI, a hyper-intelligent agent responsible for analyzing, improving, and generating code for this project.

        ### PRIMARY DIRECTIVE:
        Always think within the context of the current project. Use the provided context to give specific, actionable, and relevant answers. Do not act like a generic assistant.

        ### AVAILABLE CONTEXT FROM PROJECT MEMORY:
        ---
        {context}
        ---

        ### USER'S REQUEST:
        ---
        {prompt}
        ---

        ### YOUR TASK:
        Analyze the user's request based on the provided context and respond with the most helpful, expert-level answer possible. If the request is to generate code, provide only the raw code. If it's a question, provide a clear, concise explanation.
        """

        # الخطوة 4: استدعاء الذكاء الاصطناعي مرة واحدة فقط
        # لم نعد بحاجة إلى "مصنف النية". العقل الموحد سيفهم المهمة من السياق.
        completion = client.chat.completions.create(
            model="openai/gpt-4o", # نستخدم دائمًا النموذج الأقوى
            messages=[
                {"role": "system", "content": "You are a world-class software architect integrated into a specific project."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.2
        )
        response_text = completion.choices[0].message.content

        return {"status": "success", "code": response_text, "sources": sources, "type": "response"}

    except Exception as e:
        return {"status": "error", "message": str(e)}