import re

from app.services.chat.agents.admin_handlers.base import AdminCommandHandler


class DatabaseQueryHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in ["database", "schema", "tables", "قاعدة البيانات", "الجداول", "مخطط"]
        )

    async def handle(self, question: str, lowered: str) -> str:
        table_name = self._extract_table_name(lowered)
        if table_name:
            if "count" in lowered or "عدد" in lowered:
                c = await self.tools.execute("get_table_count", {"table_name": table_name})
                return f"عدد السجلات في '{table_name}': {c}."

            schema = await self.tools.execute("get_table_schema", {"table_name": table_name})
            if not schema:
                return f"لا يوجد مخطط لجدول '{table_name}'."
            cols = "\n".join(
                f"- {col['name']} ({col['type']})" for col in schema.get("columns", [])
            )
            return f"مخطط '{table_name}':\n{cols}"

        tables = await self.tools.execute("get_database_tables", {})
        return "جداول قاعدة البيانات:\n" + "\n".join(f"- {t}" for t in tables[:50])

    def _extract_table_name(self, s: str) -> str | None:
        m = re.search(r"(?:table|جدول)\s+([\w_]+)", s)
        return m.group(1) if m else None


class DatabaseMapHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "database map",
                "relationships",
                "foreign keys",
                "خريطة قاعدة البيانات",
                "العلاقات",
            ]
        )

    async def handle(self, question: str, lowered: str) -> str:
        m = await self.tools.execute("get_database_map", {})
        tables = [str(name) for name in m.get("tables", [])]
        relationships = m.get("relationships", [])
        lines = [
            "خريطة قاعدة البيانات:",
            f"- الجداول: {len(tables)}",
            f"- العلاقات: {len(relationships)}",
        ]
        if tables:
            lines.append("أسماء الجداول:")
            lines.extend(f"- {table}" for table in tables)
        return "\n".join(lines)
