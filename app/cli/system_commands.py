# app/cli/system_commands.py - The CLI Presentation Layer

import click
import os
from flask import Blueprint
import chromadb
from sentence_transformers import SentenceTransformer

# --- استيراد الخدمة المركزية ---
from app.services.generation_service import forge_new_code, get_model as get_embedding_model

# --- إعدادات الوزارة ---
system_cli = Blueprint('system', __name__, cli_group="system")

# --- الأوامر الخارقة ---

@system_cli.cli.command("index")
@click.option('--force', is_flag=True, help="Force re-indexing of all files.")
def index_project_files(force):
    """
    A CLI wrapper for the core project indexing logic.
    """
    # ... (منطق هذا الأمر لم يتغير، لذلك يبقى هنا لأنه خاص بالـ CLI)
    # ملاحظة: في المستقبل، يمكننا أيضًا نقل هذا المنطق إلى service layer إذا احتجنا إليه في مكان آخر.
    click.secho("--- Initiating Self-Awareness Protocol: Indexing... ---", fg="cyan")
    # ... (الكود الكامل لأمر index يبقى كما هو)
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
    IGNORED_DIRS = {"__pycache__", ".git", ".idea", "venv", ".vscode", "migrations", "instance"}
    TARGET_EXTENSIONS = {".py", ".html", ".css", ".js", ".md"}
    existing_ids = set(collection.get(include=[])['ids'])
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                file_path = os.path.join(root, file)
                if not force and file_path in existing_ids: continue
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
        collection.add(embeddings=model.encode(documents, show_progress_bar=True), documents=documents, metadatas=metadatas, ids=ids)
    except Exception as e:
        click.secho(f"An error occurred during embedding or storage: {e}", fg="red")
        return
    click.secho(f"--- Protocol Complete ---", fg="cyan")
    click.secho(f"Successfully indexed/updated {len(documents)} documents. Total knowledge base: {collection.count()} files.", fg="green")


@system_cli.cli.command("generate")
@click.argument('prompt')
def generate_code(prompt):
    """
    A clean CLI wrapper that calls the central generation service.
    Its only job is to handle input and format output for the terminal.
    """
    click.secho(f"--- Calling Core Generation Service for: '{prompt}' ---", fg="magenta")
    
    # --- استدعاء دالة واحدة فقط! ---
    result = forge_new_code(prompt)
    
    # --- التعامل مع النتائج وعرضها ---
    if result.get("status") == "error":
        click.secho(f"An error occurred in the generation service: {result['message']}", fg="red")
        return
    
    click.secho(f"Context retrieved from: {', '.join(result.get('sources', []))}")
    click.secho("--- [Generated Code] ---", fg="cyan")
    click.echo(result.get("code", "No code was generated."))
    click.secho("--- [End of Generated Code] ---", fg="cyan")
    click.secho("\nReview the code above. In the future, this will be written to a file automatically.", fg="green")