#!/usr/bin/env python3
"""واجهة تشغيل موحدة لإعادة استخدام أوامر CLI دون تكرار المنطق."""

from __future__ import annotations

from app.cli import cli as app_cli

# نعيد تصدير كائن CLI المزود من التطبيق لضمان سلوك موحد وبسيط للمستخدمين الجدد.
cli = app_cli


if __name__ == "__main__":
    cli()
