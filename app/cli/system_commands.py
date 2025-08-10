# app/cli/system_commands.py - The System's Senses and Creative Will (Fully Activated)

import click
import os
import requests # لإجراء استدعاءات API إلى العقل الخالق
from flask import Blueprint
import chromadb
from sentence_transformers import SentenceTransformer
import time

# --- إعدادات الوزارة ---
system_cli = Blueprint('system', __name__, cli_group="system")

# --- الأدوات المعرفية للوزارة ---
IGNORED_DIRS = {
    "__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance"
}
TARGET_EXTENSIONS = {
    ".py", ".html", ".css", ".js", ".md"
}

# --- نموذج الفهم (يتم تحميله مرة واحدة لتحسين الأداء) ---
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Warning: Could not preload SentenceTransformer model. Will load on demand. Error: {e}")
    embedding_model = None

def get_embedding_model():
    """ دالة مساعدة لضمان تحميل النموذج. """
    global embedding_model
    if embedding_model is None:
        click.echo("Loading sentence-transformer model (on demand)...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        click.secho("Model loaded.", fg="green")
    return embedding_model

# --- الأوامر الخارقة ---

@system_cli.cli.command("index")
@click.option('--force', is_flag=True, help="Force re-indexing of all files.")
def index_project_files(force):
    """
    Scans the project, creates embeddings for code files, 
    and stores them in the vector DB (ChromaDB).
    """
    click.secho("--- Initiating Self-Awareness Protocol: Indexing... ---", fg="cyan")
    
    try:
        click.echo("Connecting to ChromaDB memory core...")
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        click.secho("Connection successful.", fg="green")
    except Exception as e:
        click.secho(f"Error connecting to ChromaDB: {e}", fg="red")
        return

    model = get_embedding_model()

    documents, metadatas, ids = [], [], []
    
    click.echo("Scanning project structure...")
    
    existing_ids = set(collection.get(include=[])['ids'])

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                file_path = os.path.join(root, file)
                if not force and file_path in existing_ids:
                    continue # تخطي الملفات المفهرسة بالفعل ما لم يتم طلب الفرض

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            documents.append(content)
                            metadatas.append({'source': file_path})
                            ids.append(file_path)
                except Exception as e:
                    click.secho(f"Could not read file {file_path}: {e}", fg="yellow")

    if not documents:
        click.secho("No new files to index. The system's knowledge is up to date.", fg="green")
        return
    
    click.echo(f"Found {len(documents)} new/modified files to index. Generating embeddings...")
    
    try:
        if force and collection.count() > 0:
            click.echo("Force mode: Clearing all old memories...")
            collection.delete(ids=list(existing_ids))

        collection.add(
            embeddings=model.encode(documents, show_progress_bar=True),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    except Exception as e:
        click.secho(f"An error occurred during embedding or storage: {e}", fg="red")
        return

    click.secho(f"--- Protocol Complete ---", fg="cyan")
    click.secho(f"Successfully indexed/updated {len(documents)} documents. Total knowledge base: {collection.count()} files.", fg="green")


@system_cli.cli.command("generate")
@click.argument('prompt')
def generate_code(prompt):
    """
    Generates new features based on a text prompt, using the
    indexed codebase as context for more accurate results.
    """
    click.secho(f"--- Initiating Creation Protocol for: '{prompt}' ---", fg="magenta")
    
    # --- الخطوة 1: الاتصال بالذاكرة وجلب السياق ---
    try:
        click.echo("Accessing memory core to find relevant context...")
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        
        model = get_embedding_model()
        query_embedding = model.encode([prompt])
        
        # استعلام الذاكرة عن أكثر 3 مستندات صلة
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=3
        )
        
        context = "\n---\n".join(results['documents'][0])
        sources = [meta['source'] for meta in results['metadatas'][0]]
        click.echo(f"Context retrieved from: {', '.join(sources)}")

    except Exception as e:
        click.secho(f"Failed to retrieve context from memory: {e}", fg="red")
        return

    # --- الخطوة 2: استدعاء العقل الخالق مع السياق ---
    try:
        click.echo("Transmitting request and context to the AI Core...")
        api_url = "http://fastapi-ai-service:8000/ai/generate/code"
        payload = {"prompt": prompt, "context": context}
        
        response = requests.post(api_url, json=payload)
        response.raise_for_status() # إظهار خطأ إذا فشل الطلب
        
        data = response.json()
        generated_code = data.get("generated_code")

        if not generated_code:
            click.secho("AI Core did not return any code.", fg="yellow")
            return
            
    except requests.exceptions.RequestException as e:
        click.secho(f"Error communicating with AI Core: {e}", fg="red")
        return
    
    # --- الخطوة 3: عرض الخليقة الجديدة ---
    click.secho("--- [Generated Code] ---", fg="cyan")
    click.echo(generated_code)
    click.secho("--- [End of Generated Code] ---", fg="cyan")
    click.secho("\nReview the code above. In the future, this will be written to a file automatically.", fg="green")