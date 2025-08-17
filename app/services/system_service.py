# app/services/system_service.py - The System Logic Ministry (v2.0 - The Smart Hand)

import os
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path # <-- [THE SMART HAND UPGRADE] - Import the powerful Path object

# --- أدوات الوزارة ---
IGNORED_DIRS = {"__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance", "tmp"}
TARGET_EXTENSIONS = {".py", ".html", ".css", ".js", ".md", ".yml", ".json", ".sh"}

def get_embedding_model():
    """Helper to load the embedding model."""
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

        # Using Pathlib for more robust path handling
        root_path = Path(".")
        for path_obj in root_path.rglob("*"):
            if any(ignored in path_obj.parts for ignored in IGNORED_DIRS):
                continue

            if path_obj.is_file() and path_obj.suffix.lower() in TARGET_EXTENSIONS:
                file_path = str(path_obj)
                if not force and file_path in existing_ids:
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if content.strip():
                            documents.append(content)
                            metadatas.append({'source': file_path})
                            ids.append(file_path)
                except Exception:
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

def query_file(file_path: str, line: int = None):
    """
    Retrieves the content of a file. If the exact path is not found,
    it performs a fuzzy search for the filename across the entire project.
    This is the "seeing" function of the system.
    """
    p = Path(file_path)
    content = None
    source = "disk" # Default source

    # --- [THE SMART HAND PROTOCOL] ---
    # 1. Try the exact path first.
    if p.exists() and p.is_file():
        pass # Path is correct, proceed.
    else:
        # 2. If it fails, perform a fuzzy search for the filename.
        file_name_to_find = p.name
        found_path = None
        
        for potential_path in Path(".").rglob(f"*{file_name_to_find}*"):
            if potential_path.is_file() and not any(ignored in potential_path.parts for ignored in IGNORED_DIRS):
                found_path = potential_path
                break # Stop at the first match
        
        if found_path:
            p = found_path # Use the correct path we found
        else:
            return {"status": "error", "message": f"File containing '{file_path}' not found anywhere in the project."}
    # --- نهاية البروتوكول ---

    # --- Attempt to read from memory first (faster) ---
    try:
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        result = collection.get(ids=[str(p)])
        if result and result.get('documents'):
            content = result['documents'][0]
            source = "indexed memory"
    except Exception:
        pass # Fail silently and fall back to disk read

    # --- Fallback to reading directly from disk ---
    if content is None:
        try:
            with p.open('r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- Process and return the final content ---
    lines = content.splitlines()
    if line is not None:
        if 1 <= line <= len(lines):
            return {"status": "success", "content": lines[line - 1], "source": source, "path": str(p), "line": line, "total_lines": len(lines)}
        else:
            return {"status": "error", "message": f"Line {line} is out of range."}
    else:
        return {"status": "success", "content": content, "source": source, "path": str(p), "total_lines": len(lines)}