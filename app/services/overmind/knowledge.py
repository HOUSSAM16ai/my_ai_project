"""
نظام معرفة المشروع لـ Overmind (Project Knowledge System).

هذا النظام يوفر لـ Overmind معرفة كاملة وشاملة عن المشروع بأكمله:
- قاعدة البيانات: الجداول، الأعمدة، العلاقات، الفهارس
- البنية: الملفات، المجلدات، التبعيات
- الإعدادات: المتغيرات البيئية، الأسرار (من GitHub Secrets)
- التوثيق: جميع الوثائق والتعليقات

المبادئ المطبقة:
- Single Source of Truth: مصدر واحد للحقيقة عن المشروع
- Self-Awareness: النظام يعرف نفسه ويفهم بنيته
- Security: الوصول الآمن للأسرار والبيانات الحساسة
- Intelligence: معلومات ذكية قابلة للاستعلام

الميزات الرئيسية:
1. Database Inspector: فحص قاعدة البيانات بالكامل
2. Schema Analyzer: تحليل البنية والعلاقات
3. Configuration Reader: قراءة جميع الإعدادات
4. Documentation Indexer: فهرسة جميع الوثائق
"""

import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.di import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)


class DatabaseKnowledge:
    """
    معرفة قاعدة البيانات (Database Knowledge).
    
    يوفر معلومات شاملة عن:
    - جميع الجداول الموجودة
    - أعمدة كل جدول مع أنواعها
    - العلاقات بين الجداول (Foreign Keys)
    - الفهارس (Indexes)
    - القيود (Constraints)
    
    الاستخدام:
        >>> async with DatabaseKnowledge() as db_knowledge:
        >>>     tables = await db_knowledge.get_all_tables()
        >>>     schema = await db_knowledge.get_table_schema("users")
    """
    
    def __init__(self) -> None:
        """تهيئة نظام معرفة قاعدة البيانات."""
        self.settings = get_settings()
        self._session: AsyncSession | None = None
        
    async def __aenter__(self):
        """فتح الجلسة عند الدخول للسياق (context manager)."""
        async for session in get_db():
            self._session = session
            break
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة عند الخروج من السياق."""
        if self._session:
            await self._session.close()
    
    async def get_all_tables(self) -> list[str]:
        """
        الحصول على قائمة جميع الجداول في قاعدة البيانات.
        
        Returns:
            list[str]: أسماء جميع الجداول
            
        مثال:
            >>> tables = await db_knowledge.get_all_tables()
            >>> print(tables)
            ['users', 'missions', 'tasks', 'chat_messages', ...]
            
        ملاحظة:
            - text() تُنشئ SQL query نصي
            - await تنتظر نتيجة العملية غير المتزامنة
            - .scalars() تُرجع قيم عمود واحد
            - .all() تُرجع جميع النتائج كقائمة
        """
        if not self._session:
            logger.error("Database session not initialized")
            return []
        
        try:
            # استعلام SQL للحصول على جميع الجداول
            # information_schema.tables هو جدول نظام في PostgreSQL
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = await self._session.execute(query)
            tables = result.scalars().all()
            
            logger.info(f"Found {len(tables)} tables in database")
            return list(tables)
            
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    async def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """
        الحصول على البنية الكاملة لجدول معين.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            dict: معلومات شاملة عن الجدول تشمل:
                - columns: الأعمدة مع أنواعها
                - primary_keys: المفاتيح الأساسية
                - foreign_keys: المفاتيح الأجنبية
                - indexes: الفهارس
                
        مثال:
            >>> schema = await db_knowledge.get_table_schema("users")
            >>> print(schema['columns'])
            [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False},
                {'name': 'email', 'type': 'VARCHAR', 'nullable': False},
                ...
            ]
            
        ملاحظة:
            - {} تُنشئ dictionary فارغ
            - [] تُنشئ list فارغة
            - List comprehension: [expr for item in list]
            - .get() method آمنة للوصول للقيم
        """
        if not self._session:
            logger.error("Database session not initialized")
            return {}
        
        try:
            # جمع كل مكونات البنية
            columns = await self._fetch_table_columns(table_name)
            primary_keys = await self._fetch_primary_keys(table_name)
            foreign_keys = await self._fetch_foreign_keys(table_name)
            
            schema = self._build_schema_object(
                table_name, columns, primary_keys, foreign_keys
            )
            
            self._log_schema_info(table_name, columns, primary_keys, foreign_keys)
            
            return schema
            
        except Exception as e:
            logger.error(f"Error getting schema for '{table_name}': {e}")
            return {}

    async def _fetch_table_columns(self, table_name: str) -> list[dict[str, Any]]:
        """
        استعلام معلومات الأعمدة من قاعدة البيانات.
        
        Fetch column information from the database.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            قائمة بمعلومات الأعمدة
        """
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
        
        columns = []
        for row in result:
            columns.append({
                "name": row.column_name,
                "type": row.data_type,
                "nullable": row.is_nullable == "YES",
                "default": row.column_default,
                "max_length": row.character_maximum_length,
            })
        
        return columns

    async def _fetch_primary_keys(self, table_name: str) -> list[str]:
        """
        استعلام المفاتيح الأساسية من قاعدة البيانات.
        
        Fetch primary keys from the database.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            قائمة بأسماء أعمدة المفاتيح الأساسية
        """
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
        
        return [row.attname for row in pk_result]

    async def _fetch_foreign_keys(self, table_name: str) -> list[dict[str, str]]:
        """
        استعلام المفاتيح الأجنبية من قاعدة البيانات.
        
        Fetch foreign keys from the database.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            قائمة بمعلومات المفاتيح الأجنبية
        """
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
        
        foreign_keys = []
        for row in fk_result:
            foreign_keys.append({
                "column": row.column_name,
                "references_table": row.foreign_table_name,
                "references_column": row.foreign_column_name,
            })
        
        return foreign_keys

    def _build_schema_object(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        primary_keys: list[str],
        foreign_keys: list[dict[str, str]]
    ) -> dict[str, Any]:
        """
        بناء كائن البنية من المكونات المجمعة.
        
        Build schema object from collected components.
        
        Args:
            table_name: اسم الجدول
            columns: قائمة الأعمدة
            primary_keys: قائمة المفاتيح الأساسية
            foreign_keys: قائمة المفاتيح الأجنبية
            
        Returns:
            كائن البنية الكامل
        """
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "total_columns": len(columns),
        }

    def _log_schema_info(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        primary_keys: list[str],
        foreign_keys: list[dict[str, str]]
    ) -> None:
        """
        تسجيل معلومات البنية في السجل.
        
        Log schema information.
        
        Args:
            table_name: اسم الجدول
            columns: قائمة الأعمدة
            primary_keys: قائمة المفاتيح الأساسية
            foreign_keys: قائمة المفاتيح الأجنبية
        """
        logger.info(
            f"Retrieved schema for '{table_name}': "
            f"{len(columns)} columns, "
            f"{len(primary_keys)} PKs, "
            f"{len(foreign_keys)} FKs"
        )
    
    async def get_table_count(self, table_name: str) -> int:
        """
        عد السجلات في جدول معين.
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            int: عدد السجلات
            
        مثال:
            >>> count = await db_knowledge.get_table_count("users")
            >>> print(f"Total users: {count}")
        """
        if not self._session:
            return 0
        
        try:
            # استعلام COUNT لعد السجلات
            query = text(f"SELECT COUNT(*) FROM {table_name}")
            result = await self._session.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Error counting rows in '{table_name}': {e}")
            return 0
    
    async def get_full_database_map(self) -> dict[str, Any]:
        """
        الحصول على خريطة كاملة لقاعدة البيانات.
        
        Returns:
            dict: معلومات شاملة عن جميع الجداول والعلاقات
            
        مثال:
            >>> db_map = await db_knowledge.get_full_database_map()
            >>> print(json.dumps(db_map, indent=2))
            
        ملاحظة:
            - هذه دالة مكلفة (expensive) لأنها تستعلم عن كل جدول
            - استخدمها فقط عند الحاجة الحقيقية
        """
        tables = await self.get_all_tables()
        
        database_map = {
            "total_tables": len(tables),
            "tables": {},
            "relationships": [],
        }
        
        # جمع معلومات كل جدول
        for table_name in tables:
            schema = await self.get_table_schema(table_name)
            count = await self.get_table_count(table_name)
            
            database_map["tables"][table_name] = {
                "schema": schema,
                "row_count": count,
            }
            
            # استخراج العلاقات
            for fk in schema.get("foreign_keys", []):
                database_map["relationships"].append({
                    "from_table": table_name,
                    "from_column": fk["column"],
                    "to_table": fk["references_table"],
                    "to_column": fk["references_column"],
                })
        
        logger.info(
            f"Created full database map: {len(tables)} tables, "
            f"{len(database_map['relationships'])} relationships"
        )
        
        return database_map


class ProjectKnowledge:
    """
    معرفة المشروع الشاملة (Comprehensive Project Knowledge).
    
    يجمع معلومات من مصادر متعددة:
    - قاعدة البيانات (عبر DatabaseKnowledge)
    - نظام الملفات (الملفات والمجلدات)
    - المتغيرات البيئية (من .env أو GitHub Secrets)
    - التوثيق (ملفات MD)
    
    هذا هو "الدماغ" الذي يستخدمه Overmind لفهم المشروع.
    """
    
    def __init__(self) -> None:
        """تهيئة نظام معرفة المشروع."""
        self.settings = get_settings()
        self.project_root = Path.cwd()
        
    async def get_database_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات قاعدة البيانات.
        
        Returns:
            dict: معلومات شاملة عن قاعدة البيانات
        """
        async with DatabaseKnowledge() as db_knowledge:
            return await db_knowledge.get_full_database_map()
    
    def get_environment_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات البيئة والإعدادات.
        
        Returns:
            dict: معلومات البيئة (بدون الأسرار الحساسة في اللوج)
            
        ملاحظة:
            - لا نُرجع القيم الفعلية للأسرار
            - فقط نُشير إلى وجودها أو عدمها
        """
        env_info = {
            "environment": self.settings.ENVIRONMENT,
            "debug_mode": self.settings.DEBUG,
            "database_configured": bool(self.settings.DATABASE_URL),
            "ai_configured": bool(os.getenv("OPENROUTER_API_KEY")),
            "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        }
        
        # إضافة معلومات عن البيئة الحالية
        env_info["runtime"] = {
            "codespaces": self.settings.CODESPACES,
            "gitpod": bool(os.getenv("GITPOD_WORKSPACE_ID")),
            "local": not (self.settings.CODESPACES or os.getenv("GITPOD_WORKSPACE_ID")),
        }
        
        return env_info
    
    def get_project_structure(self) -> dict[str, Any]:
        """
        الحصول على بنية المشروع (الملفات والمجلدات).
        
        Returns:
            dict: معلومات عن بنية المشروع
        """
        app_dir = self.project_root / "app"
        
        structure = {
            "root": str(self.project_root),
            "python_files": 0,
            "directories": 0,
            "main_modules": [],
        }
        
        # عد الملفات والمجلدات
        for root, dirs, files in os.walk(app_dir):
            structure["directories"] += len(dirs)
            for file in files:
                if file.endswith(".py"):
                    structure["python_files"] += 1
        
        # قائمة المجلدات الرئيسية
        if app_dir.exists():
            structure["main_modules"] = [
                d.name for d in app_dir.iterdir()
                if d.is_dir() and not d.name.startswith("__")
            ]
        
        return structure
    
    async def get_complete_knowledge(self) -> dict[str, Any]:
        """
        الحصول على المعرفة الكاملة والشاملة عن المشروع.
        
        Returns:
            dict: معلومات شاملة من جميع المصادر
            
        مثال:
            >>> knowledge = await project_knowledge.get_complete_knowledge()
            >>> print(f"Tables: {knowledge['database']['total_tables']}")
            >>> print(f"Files: {knowledge['structure']['python_files']}")
        """
        knowledge = {
            "project_name": "CogniForge",
            "version": "1.0.0",
            "database": await self.get_database_info(),
            "environment": self.get_environment_info(),
            "structure": self.get_project_structure(),
            "timestamp": str(os.path.getmtime(self.project_root)),
        }
        
        logger.info(
            f"Generated complete project knowledge: "
            f"{knowledge['database']['total_tables']} tables, "
            f"{knowledge['structure']['python_files']} Python files"
        )
        
        return knowledge
