"""سياق أوامر CLI لتوفير تبعيات موحدة وقابلة لإعادة الاستخدام."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from logging import Logger

from click import Context, UsageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings


@dataclass(frozen=True)
class CLIContext:
    """يمثل الحزمة الموحدة لتبعيات CLI وفق مبدأ Composition Root."""

    settings: AppSettings
    logger: Logger
    session_provider: Callable[[], AsyncGenerator[AsyncSession, None]]


def get_cli_context(ctx: Context) -> CLIContext:
    """يستخرج سياق CLI ويضمن سلامة النوع قبل استعماله."""

    context = ctx.obj.get("context") if ctx.obj else None
    if not isinstance(context, CLIContext):
        raise UsageError("سياق CLI غير مُهيأ. تأكد من استدعاء الأوامر عبر واجهة cli الأساسية.")
    return context
