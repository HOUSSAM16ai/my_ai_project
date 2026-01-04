"""أوامر الصيانة العامة لضبط صحة النظام واستدامته."""

from __future__ import annotations

import click

from app.cli_handlers.context import get_cli_context


def register_maintenance_commands(root: click.Group) -> None:
    """يسجل مجموعة أوامر الصيانة ضمن واجهة CLI."""

    @root.group("maintenance")
    @click.pass_context
    def maintenance_group(ctx: click.Context) -> None:
        """حزمة أوامر الصيانة (محدودة حالياً)"""

        get_cli_context(ctx)  # يتحقق من توافر السياق حتى للأوامر المستقبلية

    @maintenance_group.command("placeholder")
    @click.pass_context
    def placeholder(ctx: click.Context) -> None:
        """يؤكد جاهزية خط أوامر الصيانة لإضافة مهام مستقبلية."""

        logger = get_cli_context(ctx).logger
        logger.info("واجهة الصيانة جاهزة لإضافة مهام جديدة.")
