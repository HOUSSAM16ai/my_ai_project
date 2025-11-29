# app/cli_handlers/db_cli.py
import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app import models  # Import models to register them
from app.core.database import async_session_factory, engine

# NOTE: We now import engine and factory from app.core.database,
# which are powered by the Unified Engine Factory.


def register_db_commands(root):
    @root.group("db")
    def db_group():
        "Database utilities"
        pass

    @db_group.command("create-all")
    @click.pass_context
    def create_all(ctx):
        """Creates all database tables."""
        logger = ctx.obj["logger"]
        logger.info("Creating all database tables...")

        async def _create():
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)

        asyncio.run(_create())
        logger.info("All database tables created.")

    @db_group.command("seed")
    @click.option("--confirm", is_flag=True, default=False)
    @click.option("--dry-run", is_flag=True, default=False)
    @click.pass_context
    def seed(ctx, confirm, dry_run):
        logger = ctx.obj["logger"]
        admin_email = os.getenv("ADMIN_EMAIL", "admin@cogniforge.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")

        if not admin_email:
            logger.error("ADMIN_EMAIL environment variable not set.")
            raise click.UsageError("ADMIN_EMAIL must be set in the environment.")

        if not confirm and not dry_run:
            logger.warning("Seeding requires --confirm")
            raise click.UsageError("Add --confirm to proceed")

        async def _seed():
            # Use factory to get session
            async with transactional_session(
                async_session_factory, logger, dry_run=dry_run
            ) as session:
                result = await session.execute(select(models.User).filter_by(email=admin_email))
                user = result.scalar()

                if not user:
                    user = models.User(email=admin_email, is_admin=True, full_name="Admin User")
                    user.set_password(admin_password)
                    session.add(user)
                    logger.info(f"User with email {admin_email} created.")
                else:
                    logger.info(f"User with email {admin_email} already exists. Updating password...")
                    user.set_password(admin_password)
                    if not user.is_admin:
                        user.is_admin = True
                        logger.info("Promoted user to admin.")
                    session.add(user)
                    logger.info("Password updated to match current ADMIN_PASSWORD.")

                logger.info("seed: completed")

        asyncio.run(_seed())


@asynccontextmanager
async def transactional_session(
    SessionFactory, logger, dry_run: bool = False
) -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        try:
            yield session
            if dry_run:
                logger.info("dry-run: rolling back.")
                await session.rollback()
            else:
                await session.commit()
                logger.info("committed transaction.")
        except Exception:
            logger.exception("exception during CLI operation; rolling back.")
            await session.rollback()
            raise
