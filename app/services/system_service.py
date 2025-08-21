# app/services/system_service.py - The Architecture-Aware Akashic Records Ministry (v6.0 - Final & Complete)

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sqlalchemy import text, exc as sqlalchemy_exc
from app import db
from flask import current_app

# --- أدوات الوزارة ---
IGNORED_DIRS = {"__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance", "tmp"}
TARGET_EXTENSIONS = {".py", ".html", ".css", ".js", ".md", ".yml", ".json", ".sh"}

# --- النموذج الموحد ---
_embedding_model = None
def get_embedding_model():
    """Helper to load the embedding model once and reuse it."""
    global _embedding_model
    if _embedding_model is None:
        current_app.logger.info("Loading embedding model for the first and only time...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

# --- وظائف الذاكرة المفاهيمية (Conceptual Memory) ---

def index_project(force=False):
    """
    Indexes the project into the immortal Supabase/pgvector memory.
    """
    try:
        model = get_embedding_model()
        
        documents_to_add = []
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
                            documents_to_add.append({"id": file_path, "content": content, "source": file_path})
                except Exception as e:
                    current_app.logger.warning(f"Could not read file {file_path}: {e}")

        with db.session.begin():
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS code_documents (
                    id TEXT PRIMARY KEY, content TEXT, source TEXT, embedding VECTOR(384));
            """))

            if force:
                current_app.logger.info("Force re-indexing: Deleting all existing documents...")
                db.session.execute(text("DELETE FROM code_documents;"))
            
            existing_ids = set(row[0] for row in db.session.execute(text("SELECT id FROM code_documents;")).fetchall())
            documents_to_add = [doc for doc in documents_to_add if doc['id'] not in existing_ids]

            if not documents_to_add:
                return {"status": "success", "indexed_count": 0, "message": "No new files to index."}
            
            current_app.logger.info(f"Embedding and inserting {len(documents_to_add)} new documents...")
            contents = [doc['content'] for doc in documents_to_add]
            embeddings = model.encode(contents, show_progress_bar=True)
            
            for i, doc in enumerate(documents_to_add):
                db.session.execute(text("""
                    INSERT INTO code_documents (id, content, source, embedding)
                    VALUES (:id, :content, :source, :embedding)
                """), {
                    "id": doc['id'], "content": doc['content'], "source": doc['source'],
                    "embedding": str(embeddings[i].tolist())
                })
            
            total_count = db.session.execute(text("SELECT COUNT(*) FROM code_documents;")).scalar()
        
        current_app.logger.info(f"Indexing complete. Total documents: {total_count}")
        return {"status": "success", "indexed_count": len(documents_to_add), "total_count": total_count}

    except sqlalchemy_exc.SQLAlchemyError as e:
        current_app.logger.error(f"Database error during indexing: {e}", exc_info=True)
        return {"status": "error", "message": f"Database operation failed: {e}"}
    except Exception as e:
        current_app.logger.error(f"Unexpected error during indexing: {e}", exc_info=True)
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}

def find_related_context(prompt_text: str) -> str:
    """
    Finds relevant context using a two-tiered, architecture-aware search.
    It prioritizes core service logic ('app/services') before searching the rest of the codebase.
    """
    n_results = current_app.config.get('CONTEXT_RESULTS_COUNT', 5)
    
    try:
        model = get_embedding_model()
        prompt_embedding = str(model.encode(prompt_text).tolist())

        sql = text("""
            WITH ranked_docs AS (
                SELECT 
                    content, embedding, source,
                    CASE WHEN source LIKE 'app/services/%' THEN 0 ELSE 1 END as priority_tier
                FROM code_documents
            )
            SELECT content, source
            FROM ranked_docs
            ORDER BY priority_tier ASC, embedding <=> :query_embedding
            LIMIT :limit;
        """)
        
        with db.session.begin():
            results = db.session.execute(sql, {
                "query_embedding": prompt_embedding,
                "limit": n_results
            }).fetchall()
        
        if not results:
            current_app.logger.info(f"No code context found for prompt: '{prompt_text[:50]}...'")
            return "No relevant code context found in the eternal memory."
            
        context = "\n\n---\n\n".join([f"--- Content from {row.source} ---\n{row.content}" for row in results])
        current_app.logger.info(f"Retrieved {len(results)} context chunks (priority on services).")
        return context

    except Exception as e:
        current_app.logger.error(f"Unexpected error during code context retrieval: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while retrieving code context."

def query_file(file_path: str):
    """
    Retrieves a file's content using a hyper-robust search protocol.
    """
    current_app.logger.info(f"Querying for file: '{file_path}'")
    
    p = Path(file_path)
    
    if p.is_file():
        current_app.logger.info(f"Found exact path match for '{file_path}'")
        file_path_str = str(p)
    else:
        current_app.logger.warning(f"Exact path '{file_path}' not found. Initiating exhaustive search.")
        file_name_to_find = p.name
        
        found_paths = list(Path(".").rglob(f"**/{file_name_to_find}"))
        
        valid_paths = [
            path for path in found_paths 
            if path.is_file() and not any(ignored in path.parts for ignored in IGNORED_DIRS)
        ]

        if not valid_paths:
            error_msg = f"File '{file_name_to_find}' not found anywhere in the project after exhaustive search."
            current_app.logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        p = valid_paths[0]
        file_path_str = str(p)
        current_app.logger.info(f"Exhaustive search found a match at: '{file_path_str}'")

    try:
        with db.session.begin():
            sql = text("SELECT content FROM code_documents WHERE id = :file_path")
            result = db.session.execute(sql, {"file_path": file_path_str}).scalar_one_or_none()
        
        if result is not None:
            current_app.logger.info(f"Retrieved '{file_path_str}' from immortal_memory.")
            return {"status": "success", "content": result, "source": "immortal_memory", "path": file_path_str}
    except Exception as e:
        current_app.logger.warning(f"Memory read for {file_path_str} failed: {e}. Falling back to disk.")

    try:
        with p.open('r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        current_app.logger.info(f"Retrieved '{file_path_str}' from disk.")
        return {"status": "success", "content": content, "source": "disk", "path": file_path_str}
    except Exception as e:
        current_app.logger.error(f"Disk read for {file_path_str} failed catastrophically: {e}", exc_info=True)
        return {"status": "error", "message": f"A critical error occurred while trying to read the file from disk: {e}"}

# --- محرك الحكمة (Wisdom Engine) ---
def find_similar_conversations(prompt_text: str) -> str:
    """
    Finds relevant past conversation turns, prioritizing those rated as 'good'.
    """
    n_results = current_app.config.get('WISDOM_RESULTS_COUNT', 3)
    
    try:
        sql = text("""
            WITH conversation_ratings AS (
                SELECT conversation_id, MAX(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) as has_good_rating
                FROM messages GROUP BY conversation_id
            )
            SELECT m.role, m.content, m.rating
            FROM messages m
            JOIN conversation_ratings cr ON m.conversation_id = cr.conversation_id
            WHERE m.role IN ('user', 'assistant')
            ORDER BY cr.has_good_rating DESC, m.timestamp DESC
            LIMIT :limit;
        """)
        
        with db.session.begin():
            results = db.session.execute(sql, {"limit": n_results * 2}).fetchall()
        
        if not results:
            return "No past conversational experiences found in the archives."
        
        formatted_examples = "Here are some relevant past experiences to consider:\n"
        for row in reversed(results):
            role_prefix = "Architect" if row.role == "user" else "AI"
            rating_prefix = f" [Wisdom: Rated '{row.rating}']" if row.rating else ""
            content_preview = (row.content[:150] + '...') if len(row.content) > 150 else row.content
            formatted_examples += f"- {role_prefix} said: \"{content_preview}\"{rating_prefix}\n"
            
        return formatted_examples.strip()

    except sqlalchemy_exc.OperationalError as e:
        current_app.logger.warning(f"Could not find similar conversations (table might not exist yet): {e}")
        return "The conversation archives are not yet available for consultation."
    except Exception as e:
        current_app.logger.error(f"Unexpected error during wisdom retrieval: {e}", exc_info=True)
        return "Error: An unexpected error occurred while consulting the archives."