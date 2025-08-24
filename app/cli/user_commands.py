# app/cli/user_commands.py - A Thin Client for the User Service

import click
from flask import Blueprint
from app.services import user_service # <-- استيراد العقل الجديد

users_cli = Blueprint('users', __name__, cli_group="users")

@users_cli.cli.command("list")
def list_users():
    """Lists all registered users by calling the user service."""
    click.secho("--- Calling User Service to Fetch Users ---", fg="cyan")
    all_users = user_service.get_all_users()
    # ... (الكود الحالي لطباعة الجدول يبقى كما هو، لأنه خاص بالعرض)
    
@users_cli.cli.command("create")
@click.argument('full_name')
@click.argument('email')
@click.argument('password')
@click.option('--admin', is_flag=True)
def create_user(full_name, email, password, admin):
    """Creates a new user by calling the user service."""
    click.secho(f"--- Calling User Service to Create User: {email} ---", fg="cyan")
    result = user_service.create_new_user(full_name, email, password, admin)
    
    if result['status'] == 'success':
        click.secho(result['message'], fg='green')
    else:
        click.secho(f"Error: {result['message']}", fg='red')

@users_cli.cli.command("init-admin")
def initialize_admin_user():
    """Ensures the admin user exists by calling the user service."""
    click.secho("--- Calling User Service to Ensure Admin Exists ---", fg="cyan")
    result = user_service.ensure_admin_user_exists()

    if result['status'] == 'success':
        click.secho(result['message'], fg='green')
    else:
        click.secho(f"Error: {result['message']}", fg='red')
