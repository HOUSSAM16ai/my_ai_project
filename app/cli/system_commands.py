# app/cli/system_commands.py - The Architect's Control Panel for the Akashic Records

import click
from flask import Blueprint

# --- استيراد "العقول" المركزية ---
# We now import the new history_service as well.
from app.services import generation_service, history_service, system_service

# --- إعدادات الوزارة ---
system_cli = Blueprint("system", __name__, cli_group="system")

# --- أوامر الذاكرة المفاهيمية (Conceptual Memory Commands) ---


@system_cli.cli.command("index")
@click.option("--force", is_flag=True, help="Force re-indexing of all files.")
def index_project_files(force):
    """Calls the central indexing service for the codebase."""
    click.secho("--- Calling Core Indexing Service ---", fg="cyan")
    with click.progressbar(length=1, label="Indexing project...") as bar:
        result = system_service.index_project(force)
        bar.update(1)

    if result["status"] == "error":
        click.secho(f"\nError: {result['message']}", fg="red")
        return

    if result["indexed_count"] == 0:
        click.secho("\nSystem knowledge is already up to date.", fg="yellow")
    else:
        click.secho(
            f"\nSuccessfully indexed/updated {result['indexed_count']} documents.", fg="green"
        )
    click.secho(
        f"Total knowledge base now contains {result.get('total_count', 'N/A')} files.", fg="blue"
    )


@system_cli.cli.command("query")
@click.argument("file_path")
@click.option("--line", default=None, type=int, help="Specify a line number to retrieve.")
def query_file_content(file_path, line):
    """Calls the central query service to retrieve file content."""
    click.secho(f"--- Calling Core Query Service for: {file_path} ---", fg="cyan")
    result = system_service.query_file(file_path, line)

    if result["status"] == "error":
        click.secho(f"Error: {result['message']}", fg="red")
        return

    click.secho(f"Content retrieved from {result.get('source', 'unknown')}.", fg="blue")

    if "line" in result:
        click.secho(
            f"Line {result['line']}/{result.get('total_lines', 'N/A')} in '{result.get('path', file_path)}':",
            fg="green",
        )
    else:
        click.secho(
            f"Full content of '{result.get('path', file_path)}' ({result.get('total_lines', 'N/A')} lines):",
            fg="green",
        )

    click.echo(result["content"])


# --- أوامر العقل الخالق (Generative Mind Commands) ---


@system_cli.cli.command("generate")
@click.argument("prompt")
def generate_code(prompt):
    """Calls the central generation service to get an AI response."""
    click.secho(f"--- Calling Core Generation Service for: '{prompt}' ---", fg="magenta")
    # Here we don't use a progress bar because the duration is unknown.
    result = generation_service.forge_new_code(prompt)

    if result.get("status") == "error":
        click.secho(f"An error occurred: {result['message']}", fg="red")
        return

    click.secho(f"Context from: {', '.join(result.get('sources', []))}", fg="yellow")
    click.secho("--- [AI Response] ---", fg="cyan")
    click.echo(result.get("code", "No response was generated."))
    click.secho("--- [End of Response] ---", fg="cyan")


# --- [THE WISDOM ENGINE - PHASE 3 COMMANDS] ---
# These are the new tools to interact with the immortal conversation memory.


@system_cli.cli.command("history")
@click.option("--limit", default=5, type=int, help="Number of recent conversations to display.")
def show_history(limit):
    """Displays the most recent conversation history from the database."""
    click.secho(
        f"--- Fetching last {limit} conversations from the Akashic Records ---", fg="magenta"
    )
    conversations = history_service.get_recent_conversations(limit)

    if not conversations:
        click.secho("No conversation history found.", fg="yellow")
        return

    for conv in conversations:
        click.secho(
            f"\n[Conversation ID: {conv.id} | User: {conv.user.email} | Started: {conv.start_time.strftime('%Y-%m-%d %H:%M')}]",
            bg="blue",
            fg="white",
        )
        if not conv.messages:
            click.secho("  (No messages in this conversation)", fg="yellow")
            continue
        for msg in conv.messages:
            role_color = {
                "user": "white",
                "assistant": "cyan",
                "tool": "yellow",
                "system": "magenta",
            }.get(msg.role, "white")
            rating_str = f" [Rating: {msg.rating}]" if msg.rating else ""
            content_preview = (msg.content[:200] + "...") if len(msg.content) > 200 else msg.content
            click.secho(
                f"  > [{msg.id}] {msg.role.upper()}{rating_str}: {content_preview}", fg=role_color
            )


@system_cli.cli.command("rate")
@click.argument("message_id", type=int)
@click.argument("rating", type=click.Choice(["good", "bad", "neutral"], case_sensitive=False))
def rate_message(message_id, rating):
    """Rates a specific message to provide feedback for the AI's learning loop."""
    click.secho(f"--- Submitting feedback for Message ID {message_id} as '{rating}' ---", fg="cyan")
    result = history_service.rate_message_in_db(message_id, rating)

    if result.get("status") == "success":
        click.secho(result["message"], fg="green")
    else:
        click.secho(f"Error: {result['message']}", fg="red")


# --- نهاية أدوات محرك الحكمة ---
