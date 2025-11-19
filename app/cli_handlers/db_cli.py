# app/cli_handlers/db_cli.py
import os
from collections.abc import Generator
from contextlib import contextmanager

import click
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from app import models  # Import models to register them
from app.db.session import SessionLocal, engine


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
        SQLModel.metadata.create_all(bind=engine)
        logger.info("All database tables created.")

    @db_group.command("seed")
    @click.option("--confirm", is_flag=True, default=False)
    @click.option("--dry-run", is_flag=True, default=False)
    @click.pass_context
    def seed(ctx, confirm, dry_run):
        logger = ctx.obj["logger"]
        admin_email = os.getenv("ADMIN_EMAIL")

        if not admin_email:
            logger.error("ADMIN_EMAIL environment variable not set.")
            raise click.UsageError("ADMIN_EMAIL must be set in the environment.")

        if not confirm and not dry_run:
            logger.warning("Seeding requires --confirm")
            raise click.UsageError("Add --confirm to proceed")

        with transactional_session(SessionLocal, logger, dry_run=dry_run) as session:
            user = session.query(models.User).filter_by(email=admin_email).one_or_none()
            if not user:
                user = models.User(email=admin_email, is_admin=True, full_name="Admin User")
                session.add(user)
                logger.info(f"User with email {admin_email} created.")
            else:
                logger.info(f"User with email {admin_email} already exists.")
            logger.info("seed: completed")


@contextmanager
def transactional_session(
    SessionFactory, logger, dry_run: bool = False
) -> Generator[Session, None, None]:
    session = SessionFactory()
    try:
        yield session
        if dry_run:
            logger.info("dry-run: rolling back.")
            session.rollback()
        else:
            session.commit()
            logger.info("committed transaction.")
    except Exception:
        logger.exception("exception during CLI operation; rolling back.")
        session.rollback()
        raise
    finally:
        session.close()
