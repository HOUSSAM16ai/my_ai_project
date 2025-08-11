# app/services/generation_service.py - The Multi-Task Aware Central Logic Ministry (v2.0)

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
    الدالة الأساسية للخلق، أصبحت الآن قادرة على التمييز بين
    طلبات توليد الكود والمحادثة العامة.
    """
    try:
        # --- [THE MULTI-TASK INTELLIGENCE UPGRADE] ---
        # الخطوة 1: تهيئة العميل أولاً
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "CRITICAL: OPENROUTER_API_KEY is not configured."}

        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=90.0,
        )

        # الخطوة 2: نطلب من الذكاء الاصطناعي تصنيف النية
        intent_classifier_prompt = f"""
        Analyze the user's prompt and classify its primary intent.
        Is the user asking for code generation, modification, or a technical implementation?
        Or is it a general conversational question (like a greeting, a question about its status, etc.)?
        Respond with a single word in uppercase: CODE or CHAT.

        User prompt: "{prompt}"
        """
        
        intent_completion = client.chat.completions.create(
            model="openai/gpt-4o-mini", # نموذج سريع ورخيص للتصنيف
            messages=[{"role": "user", "content": intent_classifier_prompt}],
            max_tokens=5,
            temperature=0.0
        )
        intent = intent_completion.choices[0].message.content.strip().upper()

        # --- نهاية الترقية ---

        if "CHAT" in intent:
            # إذا كان الطلب محادثة، نستخدم prompt مختلف تمامًا
            chat_prompt = f"You are CogniForge's Architect Assistant, a helpful and professional AI. Respond to the user's message concisely. User: '{prompt}'"
            chat_completion = client.chat.completions.create(
                model="openai/gpt-4o-mini", # نموذج سريع للمحادثة
                messages=[{"role": "user", "content": chat_prompt}]
            )
            response_text = chat_completion.choices[0].message.content
            return {"status": "success", "code": response_text, "sources": [], "type": "chat"}

        # --- إذا كان الطلب CODE، نستمر في المنطق الأصلي ---
        # 1. جلب السياق من الذاكرة
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        model = get_model()
        query_embedding = model.encode([prompt])
        results = collection.query(query_embeddings=query_embedding.tolist(), n_results=5)
        context = "\n---\n".join(results['documents'][0]) if results['documents'] else "No relevant context found."
        sources = [meta['source'] for meta in results['metadatas'][0]] if results['metadatas'] else []

        # 2. الاتصال بالذكاء الاصطناعي مع prompt توليد الكود
        system_prompt = f"""
        You are an expert Flask and Python developer... (نفس الـ prompt الطويل)

        **User's Request:**
        {prompt}
        **Relevant Code Context from the project:**
        ---
        {context}
        ---
        ...
        """
        
        completion = client.chat.completions.create(
            model="openai/gpt-4o", # نموذج قوي لتوليد الكود
            messages=[
                {"role": "system", "content": "You are a world-class code generation engine."},
                {"role": "user", "content": system_prompt},
            ],
            temperature=0.2
        )
        generated_code = completion.choices[0].message.content
        
        return {"status": "success", "code": generated_code, "sources": sources, "type": "code"}

    except Exception as e:
        return {"status": "error", "message": str(e)}