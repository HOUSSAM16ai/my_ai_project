# app/services/system_service.py - The System Logic Ministry (v3.1 - The Atomic Scribe)

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from app import db # <-- The central database object

# --- أدوات الوزارة ---
IGNORED_DIRS = {"__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance", "tmp"}
TARGET_EXTENSIONS = {".py", ".html", ".css", ".js", ".md", ".yml", ".json", ".sh"}

# --- [Singleton Pattern] Load the model once to save resources ---
_embedding_model = None

def get_embedding_model():
    """Helper to load the embedding model once and reuse it."""
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model for the first and only time...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def index_project(force=False):
    """
    Indexes the project into the immortal Supabase/pgvector memory using a single,
    atomic transaction for safety and efficiency.
    """
    try:
        model = get_embedding_model()
        
        documents_to_add = []
        # --- Pre-computation outside the transaction ---
        # We gather all file data before starting the database conversation.
        root_path = Path(".")
        for path_obj in root_path.rglob("*"):
            if any(ignored in path_obj.parts for ignored in IGNORED_DIRS):
                continue

            if path_obj.is_file() and path_obj.suffix.lower() in TARGET_EXTENSIONS:
                file_path = str(path_obj)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if content.strip():
                            documents_to_add.append({
                                "id": file_path,
                                "content": content,
                                "source": file_path
                            })
                except Exception:
                    pass
        
        # --- [THE SINGLE, ATOMIC TRANSACTION PROTOCOL] ---
        # The entire conversation with the database happens here.
        # If any part fails, the whole thing is rolled back.
        with db.session.begin():
            # 1. Create the table if it doesn't exist
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS code_documents (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    source TEXT,
                    embedding VECTOR(384)
                );
            """))

            # 2. If forcing, delete all existing documents
            if force:
                print("Force re-indexing: Deleting all existing documents...")
                db.session.execute(text("DELETE FROM code_documents;"))

            # 3. Filter out documents that already exist (if not forcing)
            if not force:
                existing_ids = set(row[0] for row in db.session.execute(text("SELECT id FROM code_documents;")).fetchall())
                documents_to_add = [doc for doc in documents_to_add if doc['id'] not in existing_ids]

            if not documents_to_add:
                # We need to commit the CREATE TABLE even if there's nothing to add.
                # The 'with db.session.begin()' handles this automatically.
                return {"status": "success", "indexed_count": 0, "message": "No new files to index."}
            
            # 4. Batch embedding and insertion for performance
            print(f"Embedding and inserting {len(documents_to_add)} new documents...")
            contents = [doc['content'] for doc in documents_to_add]
            embeddings = model.encode(contents, show_progress_bar=True)
            
            for i, doc in enumerate(documents_to_add):
                db.session.execute(text("""
                    INSERT INTO code_documents (id, content, source, embedding)
                    VALUES (:id, :content, :source, :embedding)
                """), {
                    "id": doc['id'], 
                    "content": doc['content'], 
                    "source": doc['source'], 
                    "embedding": str(embeddings[i].tolist())
                })
            
            # 5. Get the final count from within the transaction
            total_count = db.session.execute(text("SELECT COUNT(*) FROM code_documents;")).scalar()
        
        # The transaction is automatically committed here upon successful exit.
        return {"status": "success", "indexed_count": len(documents_to_add), "total_count": total_count}

    except Exception as e:
        # The transaction is automatically rolled back here if any error occurred.
        return {"status": "error", "message": f"Indexing failed: {e}"}


def find_related_context(prompt_text: str, n_results: int = 5) -> str:
    """
    Finds relevant context from the immortal memory using vector search.
    This is the "memory retrieval" function.
    """
    try:
        model = get_embedding_model()
        prompt_embedding = model.encode(prompt_text)

        # --- [PGVECTOR MAGIC] - Perform a semantic search query ---
        sql = text("""
            SELECT content
            FROM code_documents
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit;
        """)
        # Use a new session for read-only queries for safety
        with db.session.begin():
            results = db.session.execute(sql, {
                "query_embedding": str(prompt_embedding.tolist()),
                "limit": n_results
            }).fetchall()
        
        if not results:
            return "No relevant context found in the eternal memory."
            
        context = "\n\n---\n\n".join([row[0] for row in results])
        return context

    except Exception as e:
        print(f"Context retrieval failed: {e}")
        return f"Error retrieving context: {e}"

def query_file(file_path: str):
    """
    Retrieves a file's content, prioritizing memory, then disk, with fuzzy search fallback.
    """
    p = Path(file_path)
    
    # --- [THE SMART HAND PROTOCOL - FUZZY SEARCH] ---
    # This logic remains the same. First, we find the correct path.
    if not (p.exists() and p.is_file()):
        file_name_to_find = p.name
        found_path = None
        for potential_path in Path(".").rglob(f"*{file_name_to_find}*"):
            if potential_path.is_file() and not any(ignored in potential_path.parts for ignored in IGNORED_DIRS):
                found_path = potential_path
                break
        if not found_path:
            return {"status": "error", "message": f"File containing '{file_path}' not found anywhere in the project."}
        p = found_path
    
    # Now that we have the definite path `p`, we can proceed.
    file_path_str = str(p)

    # --- [TWO-LAYER MEMORY PROTOCOL] ---
    # 1. Attempt to read from Supabase immortal memory first
    try:
        with db.session.begin():
            sql = text("SELECT content FROM code_documents WHERE id = :file_path")
            result = db.session.execute(sql, {"file_path": file_path_str}).scalar_one_or_none()
        
        if result is not None:
            return {"status": "success", "content": result, "source": "immortal_memory", "path": file_path_str}
    except Exception as e:
        print(f"Memory read for {file_path_str} failed: {e}") # Log error but continue

    # 2. Fallback to reading directly from disk
    try:
        with p.open('r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return {"status": "success", "content": content, "source": "disk", "path": file_path_str}
    except Exception as e:
        return {"status": "error", "message": f"Disk read for {file_path_str} failed: {e}"}