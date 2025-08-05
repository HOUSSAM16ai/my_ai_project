# app/cli/user_commands.py - The User Management Division of the CMD Engine

import click
from flask import Blueprint
from app import db
from app.models import User

# 1. We create a Blueprint specifically for CLI commands related to users.
#    The `cli_group` parameter creates a new top-level command group, e.g., `flask users ...`
users_cli = Blueprint('users', __name__, cli_group="users")

@users_cli.cli.command("list")
def list_users():
    """
    [Supercharged Command] Lists all registered users in the system.
    Provides a quick overview of the user base.
    """
    click.secho("--- Fetching All System Users ---", fg="cyan")
    all_users = User.query.order_by(User.id).all()
    
    if not all_users:
        click.secho("No users found in the system.", fg="yellow")
        return
        
    # Prepare a formatted table for output
    headers = ["ID", "Full Name", "Email"]
    rows = [[user.id, user.full_name, user.email] for user in all_users]
    
    # Calculate column widths for neat printing
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if len(str(cell)) > col_widths[i]:
                col_widths[i] = len(str(cell))

    # Print header
    header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
    click.echo(header_line)
    click.echo("-|-".join("-" * width for width in col_widths))

    # Print rows
    for row in rows:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        click.echo(row_line)

    click.secho(f"\nTotal Users: {len(all_users)}", fg="green")

@users_cli.cli.command("create")
@click.argument('full_name')
@click.argument('email')
@click.argument('password')
def create_user(full_name, email, password):
    """
    [Supercharged Command] Creates a new user directly from the command line.
    Usage: flask users create "Your Name" "email@example.com" "yourpassword"
    """
    click.secho(f"--- Creating New User: {email} ---", fg="cyan")
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        click.secho(f"Error: User with email '{email}' already exists.", fg="red")
        return
        
    new_user = User(full_name=full_name, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    click.secho(f"Success! User '{full_name}' created with ID {new_user.id}.", fg="green")

# You can add more user-related commands here in the future,
# like `flask users delete <email>` or `flask users grant-admin <email>`