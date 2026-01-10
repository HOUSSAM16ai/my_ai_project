"""
مدير الأعمدة (Column Manager).

مسؤول عن إدارة الأعمدة: إضافة، حذف.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.services.overmind.database_tools.operations_logger import OperationsLogger

logger = get_logger(__name__)


class ColumnManager:
    """مدير الأعمدة في قاعدة البيانات."""

    def __init__(
        self,
        session: AsyncSession,
        operations_logger: OperationsLogger,
    ) -> None:
        """
        تهيئة مدير الأعمدة.

        Args:
            session: جلسة قاعدة البيانات
            operations_logger: مسجل العمليات
        """
        self._session = session
        self._logger = operations_logger

    async def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> dict[str, Any]:
        """
        إضافة عمود جديد إلى جدول موجود.

        Args:
            table_name: اسم الجدول
            column_name: اسم العمود الجديد
            column_type: نوع العمود (مثل: VARCHAR(255), INTEGER)

        Returns:
            dict: نتيجة الإضافة
        """
        try:
            alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}'

            await self._session.execute(text(alter_sql))
            await self._session.commit()

            result = {
                "success": True,
                "table_name": table_name,
                "column_name": column_name,
                "column_type": column_type,
            }

            self._logger.log_operation("add_column", result)
            return result

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error adding column: {e}")

            result = {
                "success": False,
                "table_name": table_name,
                "column_name": column_name,
                "error": str(e),
            }
            self._logger.log_operation("add_column", result, success=False)
            return result

    async def drop_column(
        self,
        table_name: str,
        column_name: str,
    ) -> dict[str, Any]:
        """
        حذف عمود من جدول.

        Args:
            table_name: اسم الجدول
            column_name: اسم العمود

        Returns:
            dict: نتيجة الحذف

        تحذير:
            ⚠️ البيانات في العمود ستُحذف نهائياً!
        """
        try:
            alter_sql = f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"'

            await self._session.execute(text(alter_sql))
            await self._session.commit()

            result = {
                "success": True,
                "table_name": table_name,
                "column_name": column_name,
            }

            self._logger.log_operation("drop_column", result)
            return result

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error dropping column: {e}")

            result = {
                "success": False,
                "table_name": table_name,
                "column_name": column_name,
                "error": str(e),
            }
            self._logger.log_operation("drop_column", result, success=False)
            return result
