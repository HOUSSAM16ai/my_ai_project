# app/cli/system_commands.py - A Thin Client for the System Service Layer

import click
from flask import Blueprint

# --- استيراد "العقول" المركزية ---
from app.services import generation_service
from app.services import system_service

# --- إعدادات الوزارة ---
system_cli = Blueprint('system', __name__, cli_group="system")

# --- الأوامر الخارقة (مجرد واجهات عرض) ---

@system_cli.cli.command("index")
@click.option('--force', is_flag=True, help="Force re-indexing of all files.")
def index_project_files(force):
    """Calls the central indexing service and displays the result."""
    click.secho("--- Calling Core Indexing Service ---", fg="cyan")
    with click.progressbar(length=1, label='Indexing project...') as bar:
        result = system_service.index_project(force)
        bar.update(1)
    
    if result['status'] == 'error':
        click.secho(f"\nError: {result['message']}", fg="red")
        return
    
    if result['indexed_count'] == 0:
        click.secho("\nSystem knowledge is already up to date.", fg="yellow")
    else:
        click.secho(f"\nSuccessfully indexed/updated {result['indexed_count']} documents.", fg="green")
    click.secho(f"Total knowledge base now contains {result.get('total_count', 'N/A')} files.", fg="blue")


@system_cli.cli.command("generate")
@click.argument('prompt')
def generate_code(prompt):
    """Calls the central generation service and displays the result."""
    click.secho(f"--- Calling Core Generation Service for: '{prompt}' ---", fg="magenta")
    result = generation_service.forge_new_code(prompt)
    
    if result.get("status") == "error":
        click.secho(f"An error occurred: {result['message']}", fg="red")
        return
    
    click.secho(f"Context retrieved from: {', '.join(result.get('sources', []))}")
    click.secho("--- [Generated Code] ---", fg="cyan")
    click.echo(result.get("code", "No code was generated."))
    click.secho("--- [End of Generated Code] ---", fg="cyan")

@system_cli.cli.command("query")
@click.argument('file_path')
@click.option('--line', default=None, type=int, help="Specify a line number to retrieve.")
def query_file_content(file_path, line):
    """Calls the central query service and displays the result."""
    click.secho(f"--- Calling Core Query Service for: {file_path} ---", fg="cyan")
    result = system_service.query_file(file_path, line)

    if result['status'] == 'error':
        click.secho(f"Error: {result['message']}", fg="red")
        return

    click.secho(f"Content retrieved from {result['source']}.", fg="blue")
    
    if 'line' in result:
        click.secho(f"Line {result['line']}/{result['total_lines']} in '{file_path}':", fg="green")
    else:
        click.secho(f"Full content of '{file_path}' ({result['total_lines']} lines):", fg="green")
        
    click.echo(result['content'])