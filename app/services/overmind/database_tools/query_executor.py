"""
منفذ الاستعلامات (Query Executor).

مسؤول عن تنفيذ استعلامات SQL مخصصة.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.services.overmind.database_tools.operations_logger import OperationsLogger

logger = get_logger(__name__)


class QueryExecutor:
    """منفذ استعلامات SQL مخصصة."""
    
    def __init__(
        self,
        session: AsyncSession,
        operations_logger: OperationsLogger,
    ) -> None:
        """
        تهيئة منفذ الاستعلامات.
        
        Args:
            session: جلسة قاعدة البيانات
            operations_logger: مسجل العمليات
        """
        self._session = session
        self._logger = operations_logger
    
    async def execute_sql(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        تنفيذ استعلام SQL مخصص.
        
        Args:
            sql: استعلام SQL
            params: المعاملات (اختياري)
            
        Returns:
            dict: نتيجة التنفيذ
            
        تحذير:
            ⚠️ هذه دالة قوية جداً - استخدمها بحذر!
            ⚠️ تأكد من صحة الاستعلام قبل التنفيذ!
        """
        try:
            result = await self._session.execute(text(sql), params or {})
            
            # إذا كان استعلام تحديد (SELECT)، أرجع النتائج
            if sql.strip().upper().startswith("SELECT"):
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                
                return {
                    "success": True,
                    "rows": rows,
                    "row_count": len(rows),
                }
            else:
                # إذا كان استعلام تعديل، commit
                await self._session.commit()
                
                return {
                    "success": True,
                    "affected_rows": result.rowcount,
                }
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error executing SQL: {e}")
            
            return {
                "success": False,
                "error": str(e),
            }
