import asyncio
import logging
import os
import sys
from typing import Optional

# Add project root to python path
sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.engine_factory import create_unified_async_engine
from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models import User, UserRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_admin(
    email: str,
    password: str,
    name: str = "Admin User"
) -> None:
    """
    Seeds the initial admin user.
    Uses the Unified Engine Factory via the session factory.
    """
    logger.info("Starting Admin Seeding Process...")

    # Note: We use the global session factory which is already wired to the unified engine
    async with async_session_factory() as session:
        try:
            # Check if user exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"User {email} already exists. Skipping.")
                return

            # Create new admin
            hashed_password = get_password_hash(password)
            new_admin = User(
                email=email,
                hashed_password=hashed_password,
                full_name=name,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            session.add(new_admin)
            await session.commit()
            logger.info(f"✅ Admin user {email} created successfully.")

        except Exception as e:
            logger.error(f"❌ Failed to seed admin: {e}")
            await session.rollback()
            raise

async def main():
    # Get credentials from env
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "System Admin")

    await seed_admin(admin_email, admin_password, admin_name)

if __name__ == "__main__":
    asyncio.run(main())
