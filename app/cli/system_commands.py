# app/cli/system_commands.py - The CLI Presentation Layer (v2.0 - All-Seeing)

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
    Gives the system its "memory".
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
    Gives the system its "creative will".
    """
    click.secho(f"--- Calling Core Generation Service for: '{prompt}' ---", fg="magenta")
    result = forge_new_code(prompt)
    if result.get("status") == "error":
        click.secho(f"An error occurred in the generation service: {result['message']}", fg="red")
        return
    click.secho(f"Context retrieved from: {', '.join(result.get('sources', []))}")
    click.secho("--- [Generated Code] ---", fg="cyan")
    click.echo(result.get("code", "No code was generated."))
    click.secho("--- [End of Generated Code] ---", fg="cyan")
    click.secho("\nReview the code above. In the future, this will be written to a file automatically.", fg="green")


# --- [THE ALL-SEEING EYE PROTOCOL] ---
@system_cli.cli.command("query")
@click.argument('file_path')
@click.option('--line', default=None, type=int, help="Specify a line number to retrieve.")
def query_file_content(file_path, line):
    """
    Retrieves and displays the content of a specific file from memory or disk.
    Gives the system the ability to "see" its own code on demand.
    """
    click.secho(f"--- Initiating Code Query Protocol for: {file_path} ---", fg="cyan")

    content = None
    source = "disk"

    # --- الخطوة 1: محاولة القراءة من "الذاكرة" أولاً ---
    try:
        chroma_client = chromadb.HttpClient(host='chroma-db', port=8000)
        collection = chroma_client.get_or_create_collection(name="cogniforge_codebase")
        result = collection.get(ids=[file_path])
        
        if result and result.get('documents'):
            content = result['documents'][0]
            source = "indexed memory"
    except Exception:
        click.secho("Could not connect to memory core. Falling back to direct disk access.", fg="yellow")

    # --- الخطوة 2: القراءة من القرص مباشرة كخطة بديلة ---
    if content is None:
        if not os.path.exists(file_path):
            click.secho(f"Error: File '{file_path}' not found in memory or on disk.", fg="red")
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            click.secho(f"Error reading file from disk: {e}", fg="red")
            return
            
    # --- الخطوة 3: معالجة الطلب وعرض النتيجة ---
    click.secho(f"Content retrieved from {source}.", fg="blue")
    lines = content.splitlines()
    
    if line is not None:
        if 1 <= line <= len(lines):
            line_content = lines[line - 1]
            click.secho(f"Line {line} in '{file_path}':", fg="green")
            click.echo(line_content)
        else:
            click.secho(f"Error: Line {line} is out of range. File has {len(lines)} lines.", fg="red")
    else:
        click.secho(f"Full content of '{file_path}':", fg="green")
        click.echo(content)