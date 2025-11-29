#!/usr/bin/env python3
import asyncio
import os
import sys

# Ensure the app can be imported
sys.path.append(os.getcwd())

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models import User, pwd_context  # noqa: E402


async def ensure_admin():
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalars().first()

        if not admin:
            print("Admin user not found. Creating new admin...")
            admin = User(
                email="admin@example.com",
                full_name="Admin User",
                is_admin=True
            )
            # Use explicit hashing instead of assuming a mixin method is available
            admin.password_hash = pwd_context.hash(os.environ.get("RECOVERY_ADMIN_PASSWORD", "supersecret"))
            session.add(admin)
            await session.commit()
            print("Admin created successfully.")
        else:
            print("Admin user already exists.")
            # Optional: Ensure it has admin rights if it was somehow demoted
            if not admin.is_admin:
                print("User exists but is not admin. Promoting...")
                admin.is_admin = True
                await session.commit()
                print("Promoted to admin.")

if __name__ == "__main__":
    try:
        asyncio.run(ensure_admin())
    except Exception as e:
        print(f"Error ensuring admin: {e}")
        sys.exit(1)
