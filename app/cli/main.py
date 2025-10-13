# app/cli/main.py - The Command Definitions Hub (v2.0)

from __future__ import annotations

from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.table import Table

# We now import the agent's mind directly here.
from app.services.generation_service import forge_new_code

from .graph import find_routes, find_symbol, import_graph

# --- [CORE DEPENDENCIES] ---
# We import the functions that power our commands.
from .indexer import build_index
from .search import search

# --- [APPLICATION INITIALIZATION] ---
# This is the central Typer application object.
# It is EXPORTED to be used by the main `cli.py` entrypoint.
app = typer.Typer(
    add_completion=False,
    name="cogni",
    help="CogniForge Supercharged CLI - Your repo-native architect.",
)
console = Console()

# --- [COMMAND DEFINITIONS] ---
# All of these commands will be automatically attached to the `app` object.


@app.command(help="Index the project and build vector embeddings for semantic context.")
def index(
    root: str = typer.Option(".", help="Root path to index."),
    model: str = typer.Option(None, help="Embedding model name."),
    chunk: int = typer.Option(1200, help="Chunk size in characters."),
    overlap: int = typer.Option(200, help="Overlap size in characters."),
):
    # This command remains unchanged. It is perfect.
    meta = build_index(root=root, model_name=model, chunk_chars=chunk, overlap=overlap)
    console.print("[green]Index created successfully.[/green]")
    console.print_json(data=meta)


@app.command(help="Perform a semantic search over the project.")
def query(q: str = typer.Argument(..., help="Search query or question"), k: int = 8):
    # This command remains unchanged. It is perfect.
    results = search(q, k=k)
    table = Table(title=f"Search Results for: {q}", box=box.SIMPLE_HEAVY)
    table.add_column("Score", justify="right")
    table.add_column("Path")
    table.add_column("Preview")
    for r in results:
        table.add_row(f"{r['score']:.3f}", r["path"], r["preview"].replace("\n", " ")[:120])
    console.print(table)


@app.command(help="Where is a symbol (function/class) defined?")
def where(name: str):
    # This command remains unchanged. It is perfect.
    root = Path(".").resolve()
    hits = find_symbol(root, name)
    if not hits:
        console.print(f"[yellow]Symbol '{name}' not found.[/yellow]")
        raise typer.Exit(code=1)
    table = Table(title=f"Definitions of '{name}'", box=box.SIMPLE_HEAVY)
    table.add_column("File")
    table.add_column("Line")
    table.add_column("Type")
    for p, line, kind in hits:
        table.add_row(str(p.relative_to(root)), str(line), kind)
    console.print(table)


@app.command(help="Show a summary of import dependencies.")
def deps():
    # This command remains unchanged. It is perfect.
    root = Path(".").resolve()
    g = import_graph(root)
    counts = {}
    for _, outs in g.items():
        for o in outs:
            counts[o] = counts.get(o, 0) + 1
    table = Table(title="Most Imported Packages/Modules", box=box.SIMPLE_HEAVY)
    table.add_column("Module")
    table.add_column("Count")
    for name, c in sorted(counts.items(), key=lambda x: -x[1])[:20]:
        table.add_row(name, str(c))
    console.print(table)


@app.command(help="Automatically discover API routes (Flask/FastAPI).")
def routes():
    # This command remains unchanged. It is perfect.
    root = Path(".").resolve()
    rows = find_routes(root)
    if not rows:
        console.print("[yellow]No routes discovered.[/yellow]")
        return
    table = Table(title="Discovered API Routes", box=box.SIMPLE_HEAVY)
    table.add_column("Method/Type")
    table.add_column("Path")
    table.add_column("Handler")
    for kind, path, src in rows:
        table.add_row(kind, path, src)
    console.print(table)


@app.command(help="Ask the agent, automatically feeding it semantic context first.")
def ask(question: str, k: int = typer.Option(8, help="Number of context chunks.")):
    # The logic of this command remains unchanged, but now it will work
    # because `cli.py` provides the necessary application context for `forge_new_code`.
    try:
        ctx_chunks = search(question, k=k)
        context = "\n\n".join(
            [f"--- Content from {c['path']} ---\n{c['preview']}" for c in ctx_chunks]
        )
    except Exception as e:
        context = f"Could not load local index: {e}. Answering without local context."
        console.print(f"[yellow]{context}[/yellow]")

    # The `try/except` block is no longer needed here as the context is now handled
    # by the main `cli.py` entrypoint.
    conversation = [
        {
            "role": "system",
            "content": "You are a repo-native assistant. Use the provided context to answer.",
        }
    ]
    conversation.append(
        {"role": "system", "content": f"--- LOCAL CONTEXT ---\n{context}\n--- END ---"}
    )

    with console.status("[bold green]Agent is thinking..."):
        # This call will now succeed because we are inside an app.app_context().
        result = forge_new_code(question, conversation_history=conversation)

    sources = result.get("sources", [])
    console.rule("[bold cyan]Agent Response[/bold cyan]")
    console.print(result.get("code") or result.get("message"))
    if sources:
        console.rule("Sources")
        [console.print(f"- {s}") for s in sources]


# --- [THE GREAT DECOUPLING] ---
# We remove the `main` function from this file.
# The responsibility of RUNNING the app now belongs solely to `cli.py`.
# This file is now only responsible for DEFINING the commands.
# def main():
#     app()
