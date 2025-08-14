# app/services/user_service.py - The User Logic Ministry

import os
from app import db
from app.models import User

def get_all_users():
    """Retrieves all users from the database."""
    return db.session.scalars(db.select(User).order_by(User.id)).all()

def create_new_user(full_name, email, password, is_admin=False):
    """Creates a new user. Returns a dict with status and message."""
    if db.session.scalar(db.select(User).filter_by(email=email)):
        return {"status": "error", "message": f"User with email '{email}' already exists."}
    
    try:
        new_user = User(full_name=full_name, email=email, is_admin=is_admin)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        admin_status = " (Admin)" if is_admin else ""
        return {"status": "success", "message": f"User '{full_name}' created with ID {new_user.id}{admin_status}."}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}

def ensure_admin_user_exists():
    """
    Ensures the admin user from .env exists and is an admin.
    Returns a dict with status and message.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME")

    if not admin_email or not admin_password or not admin_name:
        return {"status": "error", "message": "Admin environment variables not set."}
    
    try:
        user = db.session.scalar(db.select(User).filter_by(email=admin_email))
        if user:
            if user.is_admin:
                return {"status": "success", "message": f"Admin user '{admin_email}' already configured."}
            else:
                user.is_admin = True
                db.session.commit()
                return {"status": "success", "message": f"User '{admin_email}' promoted to admin."}
        else:
            new_admin = User(full_name=admin_name, email=admin_email, is_admin=True)
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            return {"status": "success", "message": f"Admin user '{admin_email}' created."}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}