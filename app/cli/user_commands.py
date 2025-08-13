# app/cli/user_commands.py - The User Management Division v2.0 (Admin-Aware Seeding)

import click
import os # <-- [THE SEEDING UPGRADE] - Import os to read environment variables
from flask import Blueprint
from app import db
from app.models import User

# 1. Blueprint for user-related CLI commands.
users_cli = Blueprint('users', __name__, cli_group="users")

@users_cli.cli.command("list")
def list_users():
    """
    [Supercharged Command] Lists all registered users in the system.
    """
    click.secho("--- Fetching All System Users ---", fg="cyan")
    # Using the modern db.session.execute with db.select for better practice
    all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    
    if not all_users:
        click.secho("No users found in the system.", fg="yellow")
        return
        
    headers = ["ID", "Full Name", "Email", "Is Admin"]
    rows = [[user.id, user.full_name, user.email, user.is_admin] for user in all_users]
    
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if len(str(cell)) > col_widths[i]:
                col_widths[i] = len(str(cell))

    header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
    click.echo(header_line)
    click.echo("-|-".join("-" * width for width in col_widths))

    for row in rows:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        click.echo(row_line)

    click.secho(f"\nTotal Users: {len(all_users)}", fg="green")

@users_cli.cli.command("create")
@click.argument('full_name')
@click.argument('email')
@click.argument('password')
@click.option('--admin', is_flag=True, help="Make this user an admin.")
def create_user(full_name, email, password, admin):
    """
    [Supercharged Command] Creates a new user.
    Usage: flask users create "Name" "email@example.com" "password" --admin
    """
    click.secho(f"--- Creating New User: {email} ---", fg="cyan")
    
    if db.session.scalar(db.select(User).filter_by(email=email)):
        click.secho(f"Error: User with email '{email}' already exists.", fg="red")
        return
        
    new_user = User(
        full_name=full_name, 
        email=email,
        is_admin=admin # <-- Set admin status based on the flag
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    admin_status = " (Admin)" if admin else ""
    click.secho(f"Success! User '{full_name}' created with ID {new_user.id}{admin_status}.", fg="green")


# --- [THE AUTOMATIC SEEDING PROTOCOL] ---
@users_cli.cli.command("init-admin")
def initialize_admin_user():
    """
    [SEED COMMAND] Creates the initial admin user from environment variables.
    This is the key to automating the "Coronation Protocol".
    It is designed to be run safely multiple times.
    """
    click.echo("--- Initiating Admin Seeding Protocol ---")
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Architect")

    if not admin_email or not admin_password:
        click.secho("Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in the .env file.", fg="red")
        return

    existing_admin = db.session.scalar(db.select(User).filter_by(email=admin_email))
    if existing_admin:
        click.secho(f"Admin user {admin_email} already exists. Protocol complete.", fg="yellow")
        return

    try:
        new_admin = User(
            full_name=admin_name,
            email=admin_email,
            is_admin=True # <-- Grant admin privileges directly
        )
        new_admin.set_password(admin_password)
        db.session.add(new_admin)
        db.session.commit()
        click.secho(f"✅ Supercharged admin user '{admin_email}' successfully created.", fg="green")
    except Exception as e:
        db.session.rollback()
        click.secho(f"Error creating admin user: {e}", fg="red")