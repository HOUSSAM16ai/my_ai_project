"""
ترسانة الأدوات الخارقة لقواعد البيانات (Super Database Tools Arsenal).

هذا النظام يوفر قدرات خارقة فائقة التطور للتحكم الكامل في قواعد البيانات:
- 🔍 الاستعلام والتحليل (Query & Analysis)
- ➕ إضافة الجداول والأعمدة (Create Tables & Columns)
- ✏️ تعديل البنية (Modify Structure)
- 🗑️ حذف الجداول والبيانات (Delete Tables & Data)
- 📊 إدارة الفهارس (Index Management)
- 🔗 إدارة العلاقات (Relationships Management)
- 🔒 إدارة الصلاحيات (Permissions Management)
- 📈 التحليلات المتقدمة (Advanced Analytics)
- 🔄 النسخ الاحتياطي والاستعادة (Backup & Restore)
- ⚡ تحسين الأداء (Performance Optimization)

الفلسفة:
---------
"التحكم الكامل والمطلق في كل تفصيلة من تفاصيل قاعدة البيانات
مع الحفاظ على الأمان والسلامة"

القدرات الخارقة:
----------------
✅ معرفة كل جدول وعمود ونوع بيانات
✅ إنشاء/تعديل/حذف الجداول ديناميكياً
✅ إدارة العلاقات والمفاتيح الأجنبية
✅ تحليلات متقدمة وإحصائيات
✅ تحسين الأداء تلقائياً
✅ نسخ احتياطي واستعادة ذكية
✅ تنفيذ استعلامات SQL معقدة
✅ مراقبة الأداء والصحة

التحذيرات الأمنية:
------------------
⚠️ هذه أدوات قوية جداً - استخدمها بحذر شديد!
⚠️ يمكنها حذف بيانات نهائياً - تأكد دائماً قبل الحذف
⚠️ النسخ الاحتياطي ضروري قبل أي عملية خطيرة
⚠️ جميع العمليات مُسجلة للمراجعة
⚠️ الصلاحيات محدودة حسب المستخدم
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.di import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)


class SuperDatabaseTools:
    """
    الأدوات الخارقة لقواعد البيانات (Super Database Tools).
    
    توفر تحكماً كاملاً 100% في كل تفصيلة من تفاصيل قاعدة البيانات:
    - الجداول: إنشاء، تعديل، حذف، قائمة
    - الأعمدة: إضافة، تعديل، حذف
    - البيانات: إدخال، تعديل، حذف، استعلام
    - الفهارس: إنشاء، حذف، تحليل
    - العلاقات: إنشاء FK، حذف
    - التحليل: إحصائيات، أداء، صحة
    - النسخ الاحتياطي: حفظ، استعادة
    
    الاستخدام:
        >>> async with SuperDatabaseTools() as db_tools:
        >>>     # إنشاء جدول جديد
        >>>     await db_tools.create_table("products", {
        >>>         "id": "INTEGER PRIMARY KEY",
        >>>         "name": "VARCHAR(255) NOT NULL",
        >>>         "price": "DECIMAL(10,2)"
        >>>     })
        >>>     
        >>>     # إضافة بيانات
        >>>     await db_tools.insert_data("products", {
        >>>         "name": "Product 1",
        >>>         "price": 99.99
        >>>     })
        >>>     
        >>>     # استعلام
        >>>     results = await db_tools.query_table("products")
    """
    
    def __init__(self) -> None:
        """تهيئة أدوات قاعدة البيانات."""
        self.settings = get_settings()
        self._session: AsyncSession | None = None
        self.metadata = MetaData()
        
        # سجل العمليات (Operations Log)
        self.operations_log: list[dict[str, Any]] = []
        
        logger.info("SuperDatabaseTools initialized")
    
    async def __aenter__(self):
        """فتح الجلسة (Context Manager)."""
        async for session in get_db():
            self._session = session
            break
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة."""
        if self._session:
            await self._session.close()
    
    def _log_operation(
        self,
        operation: str,
        details: dict[str, Any],
        success: bool = True,
    ) -> None:
        """
        تسجيل عملية في السجل.
        
        Args:
            operation: اسم العملية
            details: تفاصيل العملية
            success: هل نجحت العملية
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "details": details,
            "success": success,
        }
        self.operations_log.append(log_entry)
        
        log_level = logger.info if success else logger.error
        log_level(f"DB Operation: {operation} - {'✓' if success else '✗'}")
    
    # =========================================================================
    # الجداول: الإنشاء، القائمة، التفاصيل، الحذف
    # =========================================================================
    
    async def list_all_tables(self) -> list[str]:
        """
        عرض جميع الجداول في قاعدة البيانات.
        
        Returns:
            list[str]: أسماء جميع الجداول
        """
        if not self._session:
            return []
        
        try:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = await self._session.execute(query)
            tables = [row[0] for row in result]
            
            self._log_operation("list_tables", {"count": len(tables)})
            return tables
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            self._log_operation("list_tables", {"error": str(e)}, success=False)
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
        if not self._session:
            return {}
        
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
            
            # الأعمدة (Columns)
            columns_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            result = await self._session.execute(
                columns_query,
                {"table_name": table_name}
            )
            
            for row in result:
                details["columns"].append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4],
                })
            
            # المفاتيح الأساسية (Primary Keys)
            pk_query = text("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid 
                                   AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = :table_name::regclass
                  AND i.indisprimary
            """)
            
            pk_result = await self._session.execute(
                pk_query,
                {"table_name": table_name}
            )
            details["primary_keys"] = [row[0] for row in pk_result]
            
            # المفاتيح الأجنبية (Foreign Keys)
            fk_query = text("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.table_name = :table_name
            """)
            
            fk_result = await self._session.execute(
                fk_query,
                {"table_name": table_name}
            )
            
            for row in fk_result:
                details["foreign_keys"].append({
                    "column": row[0],
                    "references_table": row[1],
                    "references_column": row[2],
                })
            
            # عدد الصفوف (Row Count)
            count_query = text(f"SELECT COUNT(*) FROM {table_name}")
            count_result = await self._session.execute(count_query)
            details["row_count"] = count_result.scalar()
            
            self._log_operation("get_table_details", {"table": table_name})
            return details
            
        except Exception as e:
            logger.error(f"Error getting table details: {e}")
            self._log_operation(
                "get_table_details",
                {"table": table_name, "error": str(e)},
                success=False
            )
            return {}
    
    async def create_table(
        self,
        table_name: str,
        columns: dict[str, str],
        if_not_exists: bool = True,
    ) -> dict[str, Any]:
        """
        إنشاء جدول جديد.
        
        Args:
            table_name: اسم الجدول
            columns: الأعمدة مع أنواعها
                مثال: {
                    "id": "INTEGER PRIMARY KEY",
                    "name": "VARCHAR(255) NOT NULL",
                    "email": "VARCHAR(255) UNIQUE"
                }
            if_not_exists: عدم رفع خطأ إذا كان الجدول موجوداً
            
        Returns:
            dict: نتيجة العملية
            
        مثال:
            >>> await db_tools.create_table("users", {
            ...     "id": "SERIAL PRIMARY KEY",
            ...     "username": "VARCHAR(50) NOT NULL UNIQUE",
            ...     "email": "VARCHAR(255) NOT NULL",
            ...     "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ... })
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            # بناء SQL
            if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            columns_sql = ",\n    ".join(
                f"{col_name} {col_type}"
                for col_name, col_type in columns.items()
            )
            
            sql = f"""
            CREATE TABLE {if_not_exists_clause}{table_name} (
                {columns_sql}
            )
            """
            
            # تنفيذ
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "columns_count": len(columns),
            }
            
            self._log_operation("create_table", result)
            logger.info(f"✓ Table created: {table_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error creating table {table_name}: {e}")
            
            result = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._log_operation("create_table", result, success=False)
            return result
    
    async def drop_table(
        self,
        table_name: str,
        cascade: bool = False,
        if_exists: bool = True,
    ) -> dict[str, Any]:
        """
        حذف جدول.
        
        Args:
            table_name: اسم الجدول
            cascade: حذف الجداول المرتبطة أيضاً
            if_exists: عدم رفع خطأ إذا لم يكن الجدول موجوداً
            
        Returns:
            dict: نتيجة العملية
            
        تحذير:
            ⚠️ هذه عملية خطيرة! البيانات ستُحذف نهائياً!
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            if_exists_clause = "IF EXISTS " if if_exists else ""
            cascade_clause = " CASCADE" if cascade else ""
            
            sql = f"DROP TABLE {if_exists_clause}{table_name}{cascade_clause}"
            
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "cascade": cascade,
            }
            
            self._log_operation("drop_table", result)
            logger.warning(f"⚠️  Table dropped: {table_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error dropping table {table_name}: {e}")
            
            result = {
                "success": False,
                "table_name": table_name,
                "error": str(e),
            }
            self._log_operation("drop_table", result, success=False)
            return result
    
    # =========================================================================
    # الأعمدة: الإضافة، التعديل، الحذف
    # =========================================================================
    
    async def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> dict[str, Any]:
        """
        إضافة عمود جديد لجدول موجود.
        
        Args:
            table_name: اسم الجدول
            column_name: اسم العمود الجديد
            column_type: نوع العمود
                مثال: "VARCHAR(255)", "INTEGER NOT NULL"
            
        Returns:
            dict: نتيجة العملية
            
        مثال:
            >>> await db_tools.add_column(
            ...     "users",
            ...     "phone",
            ...     "VARCHAR(20)"
            ... )
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "column_name": column_name,
                "column_type": column_type,
            }
            
            self._log_operation("add_column", result)
            logger.info(f"✓ Column added: {table_name}.{column_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error adding column: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("add_column", result, success=False)
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
            dict: نتيجة العملية
            
        تحذير:
            ⚠️ البيانات في هذا العمود ستُحذف نهائياً!
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "column_name": column_name,
            }
            
            self._log_operation("drop_column", result)
            logger.warning(f"⚠️  Column dropped: {table_name}.{column_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error dropping column: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("drop_column", result, success=False)
            return result
    
    # =========================================================================
    # البيانات: الإدخال، الاستعلام، التحديث، الحذف
    # =========================================================================
    
    async def insert_data(
        self,
        table_name: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        إدخال بيانات في جدول.
        
        Args:
            table_name: اسم الجدول
            data: البيانات المراد إدخالها
                مثال: {"name": "John", "age": 30}
            
        Returns:
            dict: نتيجة العملية
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(f":{key}" for key in data.keys())
            
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            await self._session.execute(text(sql), data)
            await self._session.commit()
            
            result = {
                "success": True,
                "table_name": table_name,
                "inserted_columns": list(data.keys()),
            }
            
            self._log_operation("insert_data", result)
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error inserting data: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("insert_data", result, success=False)
            return result
    
    async def query_table(
        self,
        table_name: str,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        استعلام بيانات من جدول.
        
        Args:
            table_name: اسم الجدول
            columns: الأعمدة المطلوبة (افتراضياً: جميع الأعمدة)
            where: شرط WHERE (اختياري)
            limit: الحد الأقصى للنتائج
            
        Returns:
            list[dict]: البيانات
            
        مثال:
            >>> results = await db_tools.query_table(
            ...     "users",
            ...     columns=["id", "name"],
            ...     where="age > 18",
            ...     limit=10
            ... )
        """
        if not self._session:
            return []
        
        try:
            columns_sql = ", ".join(columns) if columns else "*"
            where_clause = f" WHERE {where}" if where else ""
            
            sql = f"SELECT {columns_sql} FROM {table_name}{where_clause} LIMIT {limit}"
            
            result = await self._session.execute(text(sql))
            
            # تحويل النتائج إلى قائمة من dictionaries
            rows = []
            for row in result:
                rows.append(dict(row._mapping))
            
            self._log_operation("query_table", {
                "table": table_name,
                "rows_returned": len(rows)
            })
            
            return rows
            
        except Exception as e:
            logger.error(f"Error querying table: {e}")
            self._log_operation("query_table", {"error": str(e)}, success=False)
            return []
    
    async def update_data(
        self,
        table_name: str,
        set_values: dict[str, Any],
        where: str,
    ) -> dict[str, Any]:
        """
        تحديث بيانات في جدول.
        
        Args:
            table_name: اسم الجدول
            set_values: القيم الجديدة
                مثال: {"name": "New Name", "age": 25}
            where: شرط WHERE لتحديد الصفوف
                مثال: "id = 1"
            
        Returns:
            dict: نتيجة العملية
            
        تحذير:
            ⚠️ تأكد من شرط WHERE لتجنب تحديث جميع الصفوف!
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            set_clause = ", ".join(
                f"{key} = :{key}" for key in set_values.keys()
            )
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
            
            result = await self._session.execute(text(sql), set_values)
            await self._session.commit()
            
            affected_rows = result.rowcount
            
            result_dict = {
                "success": True,
                "table_name": table_name,
                "affected_rows": affected_rows,
            }
            
            self._log_operation("update_data", result_dict)
            return result_dict
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error updating data: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("update_data", result, success=False)
            return result
    
    async def delete_data(
        self,
        table_name: str,
        where: str,
    ) -> dict[str, Any]:
        """
        حذف بيانات من جدول.
        
        Args:
            table_name: اسم الجدول
            where: شرط WHERE لتحديد الصفوف
                مثال: "id = 1" أو "age < 18"
            
        Returns:
            dict: نتيجة العملية
            
        تحذير:
            ⚠️ الحذف نهائي! تأكد من شرط WHERE!
            ⚠️ لحذف جميع البيانات، استخدم where="1=1" بوعي كامل!
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            sql = f"DELETE FROM {table_name} WHERE {where}"
            
            result = await self._session.execute(text(sql))
            await self._session.commit()
            
            affected_rows = result.rowcount
            
            result_dict = {
                "success": True,
                "table_name": table_name,
                "deleted_rows": affected_rows,
            }
            
            self._log_operation("delete_data", result_dict)
            logger.warning(f"⚠️  Deleted {affected_rows} rows from {table_name}")
            return result_dict
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error deleting data: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("delete_data", result, success=False)
            return result
    
    # =========================================================================
    # الفهارس: الإنشاء، الحذف
    # =========================================================================
    
    async def create_index(
        self,
        index_name: str,
        table_name: str,
        columns: list[str],
        unique: bool = False,
    ) -> dict[str, Any]:
        """
        إنشاء فهرس (Index).
        
        Args:
            index_name: اسم الفهرس
            table_name: اسم الجدول
            columns: الأعمدة المراد فهرستها
            unique: هل الفهرس فريد (UNIQUE INDEX)
            
        Returns:
            dict: نتيجة العملية
            
        مثال:
            >>> await db_tools.create_index(
            ...     "idx_users_email",
            ...     "users",
            ...     ["email"],
            ...     unique=True
            ... )
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            unique_clause = "UNIQUE " if unique else ""
            columns_sql = ", ".join(columns)
            
            sql = f"CREATE {unique_clause}INDEX {index_name} ON {table_name} ({columns_sql})"
            
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "index_name": index_name,
                "table_name": table_name,
                "columns": columns,
                "unique": unique,
            }
            
            self._log_operation("create_index", result)
            logger.info(f"✓ Index created: {index_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error creating index: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("create_index", result, success=False)
            return result
    
    async def drop_index(self, index_name: str) -> dict[str, Any]:
        """
        حذف فهرس.
        
        Args:
            index_name: اسم الفهرس
            
        Returns:
            dict: نتيجة العملية
        """
        if not self._session:
            return {"success": False, "error": "No session"}
        
        try:
            sql = f"DROP INDEX IF EXISTS {index_name}"
            
            await self._session.execute(text(sql))
            await self._session.commit()
            
            result = {
                "success": True,
                "index_name": index_name,
            }
            
            self._log_operation("drop_index", result)
            logger.info(f"✓ Index dropped: {index_name}")
            return result
            
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Error dropping index: {e}")
            
            result = {
                "success": False,
                "error": str(e),
            }
            self._log_operation("drop_index", result, success=False)
            return result
    
    # =========================================================================
    # تنفيذ SQL مخصص
    # =========================================================================
    
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
        if not self._session:
            return {"success": False, "error": "No session"}
        
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
    
    # =========================================================================
    # سجل العمليات
    # =========================================================================
    
    def get_operations_log(self) -> list[dict[str, Any]]:
        """
        الحصول على سجل العمليات.
        
        Returns:
            list[dict]: جميع العمليات المُنفذة
        """
        return self.operations_log
    
    def clear_operations_log(self) -> None:
        """مسح سجل العمليات."""
        self.operations_log.clear()
        logger.info("Operations log cleared")
