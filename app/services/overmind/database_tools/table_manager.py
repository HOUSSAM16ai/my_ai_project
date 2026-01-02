"""
مدير الجداول (Table Manager).

مسؤول عن إدارة الجداول: إنشاء، حذف، قائمة، تفاصيل.
"""

from typing import Any

from sqlalchemy import MetaData, Table, Column, Integer, String, Text, text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.services.overmind.database_tools.operations_logger import OperationsLogger

logger = get_logger(__name__)


class TableManager:
    """مدير الجداول في قاعدة البيانات."""
    
    def __init__(
        self,
        session: AsyncSession,
        metadata: MetaData,
        operations_logger: OperationsLogger,
    ) -> None:
        """
        تهيئة مدير الجداول.
        
        Args:
            session: جلسة قاعدة البيانات
            metadata: معلومات البيانات الوصفية
            operations_logger: مسجل العمليات
        """
        self._session = session
        self.metadata = metadata
        self._logger = operations_logger
    
    async def list_all_tables(self) -> list[str]:
        """
        عرض جميع الجداول في قاعدة البيانات.
        
        Returns:
            list[str]: أسماء جميع الجداول
        """
        try:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = await self._session.execute(query)
            tables = [row[0] for row in result]
            
            self._logger.log_operation("list_tables", {"count": len(tables)})
            return tables
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            self._logger.log_operation("list_tables", {"error": str(e)}, success=False)
            return []
    
    async def get_table_details(self, table_name: str) -> dict[str, Any]:
        """
        الحصول على تفاصيل كاملة عن جدول.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            dict: تفاصيل شاملة تشمل:
                - columns: الأعمدة مع أنواعها
                - primary_keys: المفاتيح الأساسية
                - foreign_keys: المفاتيح الأجنبية
                - indexes: الفهارس
                - constraints: القيود
                - row_count: عدد الصفوف
        """
        try:
            details = {
                "table_name": table_name,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
                "constraints": [],
                "row_count": 0,
            }
            
            # الأعمدة
            columns_query = text(f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            result = await self._session.execute(
                columns_query, {"table_name": table_name}
            )
            for row in result:
                details["columns"].append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3],
                })
            
            # المفاتيح الأساسية
            pk_query = text(f"""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = :table_name
                    AND tc.constraint_type = 'PRIMARY KEY'
            """)
            
            result = await self._session.execute(pk_query, {"table_name": table_name})
            details["primary_keys"] = [row[0] for row in result]
            
            # المفاتيح الأجنبية
            fk_query = text(f"""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = :table_name
                    AND tc.constraint_type = 'FOREIGN KEY'
            """)
            
            result = await self._session.execute(fk_query, {"table_name": table_name})
            for row in result:
                details["foreign_keys"].append({
                    "column": row[0],
                    "references_table": row[1],
                    "references_column": row[2],
                })
            
            # الفهارس
            idx_query = text(f"""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = :table_name
            """)
            
            result = await self._session.execute(idx_query, {"table_name": table_name})
            for row in result:
                details["indexes"].append({
                    "name": row[0],
                    "definition": row[1],
                })
            
            # عدد الصفوف
            count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
            result = await self._session.execute(count_query)
            details["row_count"] = result.scalar()
            
            self._logger.log_operation("get_table_details", {"table": table_name})
            return details
            
        except Exception as e:
            logger.error(f"Error getting table details: {e}")
            self._logger.log_operation(
                "get_table_details",
                {"table": table_name, "error": str(e)},
                success=False,
            )
            return {}
    
    async def create_table(
        self,
        table_name: str,
        columns: dict[str, str],
    ) -> dict[str, Any]:
        """
        إنشاء جدول جديد.
        
        Args:
            table_name: اسم الجدول
            columns: قاموس الأعمدة {اسم: نوع}
                مثال: {"id": "INTEGER PRIMARY KEY", "name": "VARCHAR(255)"}
        
        Returns:
            dict: نتيجة الإنشاء
        """
        try:
            # بناء استعلام CREATE TABLE
            columns_sql = ", ".join(
                [f'"{col_name}" {col_type}' for col_name, col_type in columns.items()]
            )
            
            create_sql = f'CREATE TABLE "{table_name}" ({columns_sql})'
            
            await self._session.execute(text(create_sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "columns": columns,
            }
            
            self._logger.log_operation("create_table", result)
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error creating table: {e}")
            
            result = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("create_table", result, success=False)
            return result
    
    async def drop_table(
        self,
        table_name: str,
        cascade: bool = False,
    ) -> dict[str, Any]:
        """
        حذف جدول.
        
        Args:
            table_name: اسم الجدول
            cascade: حذف التبعيات أيضاً
        
        Returns:
            dict: نتيجة الحذف
            
        تحذير:
            ⚠️ هذه عملية خطيرة - البيانات ستُحذف نهائياً!
        """
        try:
            cascade_sql = " CASCADE" if cascade else ""
            drop_sql = f'DROP TABLE IF EXISTS "{table_name}"{cascade_sql}'
            
            await self._session.execute(text(drop_sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "cascade": cascade,
            }
            
            self._logger.log_operation("drop_table", result)
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error dropping table: {e}")
            
            result = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._logger.log_operation("drop_table", result, success=False)
            return result
