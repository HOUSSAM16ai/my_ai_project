# app/cli/user_commands.py - The User Management Division v2.1 (Bulletproof Seeding)

import click
import os
from flask import Blueprint
from app import db
from app.models import User

# Blueprint for user-related CLI commands.
users_cli = Blueprint('users', __name__, cli_group="users")

@users_cli.cli.command("list")
def list_users():
    """
    [Supercharged Command] Lists all registered users in the system.
    """
    click.secho("--- Fetching All System Users ---", fg="cyan")
    all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    
    if not all_users:
        click.secho("No users found in the system.", fg="yellow")
        return
        
    headers = ["ID", "Full Name", "Email", "Is Admin"]
    rows = [[user.id, user.full_name, user.email, user.is_admin] for user in all_users]
    
    # --- Dynamic Column Width Calculation ---
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

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
        is_admin=admin
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    admin_status = " (Admin)" if admin else ""
    click.secho(f"Success! User '{full_name}' created with ID {new_user.id}{admin_status}.", fg="green")


# --- [THE BULLETPROOF AUTOMATIC SEEDING PROTOCOL] ---
@users_cli.cli.command("init-admin")
def initialize_admin_user():
    """
    [CRITICAL SEED COMMAND] Ensures the admin user exists AND is an admin.
    If the user exists but is not an admin, it promotes them.
    If the user does not exist, it creates them.
    This is the final solution to the automation race condition.
    """
    click.echo("--- Initiating Bulletproof Admin Seeding Protocol ---")
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME")

    if not all_admin_email or not admin_password or not admin_name:
        click.secho("Error: ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_NAME must be set in the .env file.", fg="red")
        return

    try:
        user = db.session.scalar(db.select(User).filter_by(email=admin_email))
        
        if user:
            # المستخدم موجود. تحقق من صلاحياته.
            if user.is_admin:
                click.secho(f"Admin user '{admin_email}' already configured. Protocol complete.", fg="yellow")
            else:
                # المستخدم موجود ولكنه ليس مشرفًا. قم بترقيته!
                click.secho(f"User '{admin_email}' found. Promoting to admin status...", fg="cyan")
                user.is_admin = True
                db.session.commit()
                click.secho(f"✅ User '{admin_email}' has been successfully promoted to admin.", fg="green")
        else:
            # المستخدم غير موجود. قم بإنشائه.
            click.secho(f"Admin user '{admin_email}' not found. Creating new admin user...", fg="cyan")
            new_admin = User(
                full_name=admin_name,
                email=admin_email,
                is_admin=True # منحه صلاحيات المشرف مباشرة
            )
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            click.secho(f"✅ Supercharged admin user '{admin_email}' successfully created.", fg="green")

    except Exception as e:
        db.session.rollback()
        click.secho(f"An unexpected error occurred during seeding: {e}", fg="red")
