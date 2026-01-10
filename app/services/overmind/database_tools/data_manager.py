"""
مدير البيانات (Data Manager).

مسؤول عن إدارة البيانات: إدخال، استعلام، تعديل، حذف.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.services.overmind.database_tools.operations_logger import OperationsLogger

logger = get_logger(__name__)


class DataManager:
    """مدير البيانات في قاعدة البيانات."""

    def __init__(
        self,
        session: AsyncSession,
        operations_logger: OperationsLogger,
    ) -> None:
        """
        تهيئة مدير البيانات.

        Args:
            session: جلسة قاعدة البيانات
            operations_logger: مسجل العمليات
        """
        self._session = session
        self._logger = operations_logger

    async def insert_data(
        self,
        table_name: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        إدخال بيانات جديدة في جدول.

        Args:
            table_name: اسم الجدول
            data: البيانات المراد إدخالها {عمود: قيمة}

        Returns:
            dict: نتيجة الإدخال
        """
        try:
            columns = ", ".join([f'"{col}"' for col in data])
            placeholders = ", ".join([f":{col}" for col in data])

            insert_sql = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'

            await self._session.execute(text(insert_sql), data)
            await self._session.commit()

            result = {
                "success": True,
                "table_name": table_name,
                "data": data,
            }

            self._logger.log_operation("insert_data", result)
            return result

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error inserting data: {e}")

            result = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("insert_data", result, success=False)
            return result

    async def query_table(
        self,
        table_name: str,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        استعلام بيانات من جدول.

        Args:
            table_name: اسم الجدول
            where: شروط الاستعلام (اختياري)
            limit: حد أقصى للنتائج
            offset: البداية

        Returns:
            dict: نتيجة الاستعلام
        """
        try:
            query = f'SELECT * FROM "{table_name}"'
            params: dict[str, Any] = {}

            if where:
                where_clauses = [f'"{col}" = :{col}' for col in where]
                query += " WHERE " + " AND ".join(where_clauses)
                params.update(where)

            if limit:
                query += f" LIMIT {limit}"

            if offset:
                query += f" OFFSET {offset}"

            result = await self._session.execute(text(query), params)
            rows = []
            for row in result:
                rows.append(dict(row._mapping))

            result_data = {
                "success": True,
                "table_name": table_name,
                "rows": rows,
                "count": len(rows),
            }

            self._logger.log_operation("query_table", {"table": table_name, "count": len(rows)})
            return result_data

        except Exception as e:
            logger.error(f"Error querying table: {e}")

            result_data = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("query_table", result_data, success=False)
            return result_data

    async def update_data(
        self,
        table_name: str,
        data: dict[str, Any],
        where: dict[str, Any],
    ) -> dict[str, Any]:
        """
        تعديل بيانات في جدول.

        Args:
            table_name: اسم الجدول
            data: البيانات الجديدة {عمود: قيمة}
            where: شروط التعديل {عمود: قيمة}

        Returns:
            dict: نتيجة التعديل
        """
        try:
            set_clauses = [f'"{col}" = :set_{col}' for col in data]
            where_clauses = [f'"{col}" = :where_{col}' for col in where]

            update_sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE {" AND ".join(where_clauses)}'

            params = {f"set_{k}": v for k, v in data.items()}
            params.update({f"where_{k}": v for k, v in where.items()})

            result = await self._session.execute(text(update_sql), params)
            await self._session.commit()

            result_data = {
                "success": True,
                "table_name": table_name,
                "affected_rows": result.rowcount,
            }

            self._logger.log_operation("update_data", result_data)
            return result_data

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error updating data: {e}")

            result_data = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("update_data", result_data, success=False)
            return result_data

    async def delete_data(
        self,
        table_name: str,
        where: dict[str, Any],
    ) -> dict[str, Any]:
        """
        حذف بيانات من جدول.

        Args:
            table_name: اسم الجدول
            where: شروط الحذف {عمود: قيمة}

        Returns:
            dict: نتيجة الحذف

        تحذير:
            ⚠️ البيانات ستُحذف نهائياً - احذر!
        """
        try:
            where_clauses = [f'"{col}" = :{col}' for col in where]

            delete_sql = f'DELETE FROM "{table_name}" WHERE {" AND ".join(where_clauses)}'

            result = await self._session.execute(text(delete_sql), where)
            await self._session.commit()

            result_data = {
                "success": True,
                "table_name": table_name,
                "affected_rows": result.rowcount,
            }

            self._logger.log_operation("delete_data", result_data)
            return result_data

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error deleting data: {e}")

            result_data = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("delete_data", result_data, success=False)
            return result_data
