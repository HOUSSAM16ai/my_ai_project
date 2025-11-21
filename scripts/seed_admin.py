import asyncio
import logging
import os
import sys

# Ensure we can import app modules
sys.path.append(os.getcwd())

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import get_connection_string  # noqa: E402
from app.models import User  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_admin():
    """
    Seeds the admin user if it doesn't exist.
    Reads ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME from environment.
    """
    logger.info("🌱 Starting Admin Seeding Process...")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin User")

    if not admin_email or not admin_password:
        logger.warning("⚠️ ADMIN_EMAIL or ADMIN_PASSWORD not set. Skipping admin creation.")
        return

    logger.info(f"Checking for admin user: {admin_email}")

    # Create Async Engine & Session
    database_url = get_connection_string()

    connect_args = {}
    if "postgresql" in database_url:
        connect_args = {
            "statement_cache_size": 0,
        }

    engine = create_async_engine(database_url, echo=False, connect_args=connect_args)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if user exists
            result = await session.execute(select(User).where(User.email == admin_email))
            user = result.scalars().first()

            if user:
                logger.info(f"✅ Admin user '{admin_email}' already exists.")
            else:
                logger.info(f"Creating new admin user '{admin_email}'...")
                new_user = User(
                    email=admin_email,
                    full_name=admin_name,
                    is_admin=True,
                )
                new_user.set_password(admin_password)
                session.add(new_user)
                await session.commit()
                logger.info(f"🎉 Admin user '{admin_email}' created successfully.")

        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_admin())
