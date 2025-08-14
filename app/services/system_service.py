# app/services/system_service.py - The System Logic Ministry

import os
import chromadb
from sentence_transformers import SentenceTransformer

# --- أدوات الوزارة ---
IGNORED_DIRS = {"__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance"}
TARGET_EXTENSIONS = {".py", ".html", ".css", ".js", ".md"}

def get_embedding_model():
    """Helper to load the embedding model."""
    # ملاحظة: في نظام إنتاجي حقيقي، قد ترغب في جعل هذا "سينجلتون" (Singleton)
    # لتجنب إعادة تحميله في كل مرة.
    print("Loading embedding model for system service...")
    return SentenceTransformer('all-MiniLM-L6-v2')

def index_project(force=False):
    """
    Pure logic for indexing the project. Returns a dict with the result.
    This is the "memory" function of the system.
    """
    try:
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        model = get_embedding_model()
        
        documents, metadatas, ids = [], [], []
        existing_ids = set(collection.get(include=[])['ids'])

        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    if not force and file_path in existing_ids:
                        continue
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                documents.append(content)
                                metadatas.append({'source': file_path})
                                ids.append(file_path)
                    except Exception:
                        # نتجاهل الملفات التي لا يمكن قراءتها بصمت في طبقة الخدمة
                        pass
        
        if not documents:
            return {"status": "success", "indexed_count": 0, "message": "No new files to index."}

        if force and collection.count() > 0:
            collection.delete(ids=list(existing_ids))

        collection.add(
            embeddings=model.encode(documents, show_progress_bar=True),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return {"status": "success", "indexed_count": len(documents), "total_count": collection.count()}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_file(file_path, line=None):
    """
    Pure logic for querying a file from memory or disk.
    This is the "seeing" function of the system.
    """
    content = None
    source = "disk"
    try:
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        result = collection.get(ids=[file_path])
        if result and result.get('documents'):
            content = result['documents'][0]
            source = "indexed memory"
    except Exception:
        pass # نتجاهل الفشل وننتقل إلى القراءة من القرص

    if content is None:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File '{file_path}' not found."}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    lines = content.splitlines()
    if line is not None:
        if 1 <= line <= len(lines):
            return {"status": "success", "content": lines[line - 1], "source": source, "line": line, "total_lines": len(lines)}
        else:
            return {"status": "error", "message": f"Line {line} is out of range."}
    else:
        return {"status": "success", "content": content, "source": source, "total_lines": len(lines)}