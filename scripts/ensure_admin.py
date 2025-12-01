#!/usr/bin/env python3
import asyncio
import os
import sys

# Ensure the app can be imported
sys.path.append(os.getcwd())

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import User, pwd_context


async def ensure_admin():
    async with async_session_factory() as session:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@cogniforge.com")
        # Use ADMIN_PASSWORD or RECOVERY_ADMIN_PASSWORD, default to "supersecret"
        admin_password = os.environ.get(
            "ADMIN_PASSWORD", os.environ.get("RECOVERY_ADMIN_PASSWORD", "supersecret")
        )

        result = await session.execute(select(User).where(User.email == admin_email))
        admin = result.scalars().first()

        if not admin:
            print(f"Admin user {admin_email} not found. Creating new admin...")
            admin = User(email=admin_email, full_name="Admin User", is_admin=True)
            admin.password_hash = pwd_context.hash(admin_password)
            session.add(admin)
            await session.commit()
            print("Admin created successfully.")
        else:
            print(f"Admin user {admin_email} already exists. Updating credentials...")
            # Repair password hash if needed or just always update to ensure consistency
            admin.password_hash = pwd_context.hash(admin_password)

            if not admin.is_admin:
                print("User exists but is not admin. Promoting...")
                admin.is_admin = True

            session.add(admin)
            await session.commit()
            print("Admin credentials updated and promoted.")


if __name__ == "__main__":
    try:
        asyncio.run(ensure_admin())
    except Exception as e:
        print(f"Error ensuring admin: {e}")
        sys.exit(1)
