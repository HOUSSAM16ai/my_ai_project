"""واجهة أوامر موحدة لإدارة التطبيق وفق مبادئ KISS وSOLID."""

from __future__ import annotations

import os
from collections.abc import Callable

import click

from app.cli_handlers.context import CLIContext
from app.cli_handlers.db_cli import register_db_commands
from app.cli_handlers.maintenance_cli import register_maintenance_commands
from app.cli_handlers.migrate_cli import register_migrate_commands
from app.core.di import get_logger, get_session, get_settings

CommandRegistrar = Callable[[click.Group], None]
COMMAND_REGISTRARS: tuple[CommandRegistrar, ...] = (
    register_db_commands,
    register_migrate_commands,
    register_maintenance_commands,
)


@click.group()
@click.option("--env", default=None, help="ملف أو وسم بيئة اختياري")
@click.pass_context
def cli(ctx: click.Context, env: str | None) -> None:
    """يمهد سياق CLI ويضبط البيئة قبل تسجيل الأوامر."""

    if env:
        os.environ["ENV_FILE"] = env

    settings = get_settings()
    logger = get_logger("cli")
    ctx.obj = {
        "context": CLIContext(
            settings=settings,
            logger=logger,
            session_provider=get_session,
        )
    }


for registrar in COMMAND_REGISTRARS:
    registrar(cli)


if __name__ == "__main__":
    cli()
