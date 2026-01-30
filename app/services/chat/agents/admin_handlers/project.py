from app.services.chat.agents.admin_handlers.base import AdminCommandHandler


class ProjectInfoHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "project",
                "structure",
                "architecture",
                "المشروع",
                "بنية المشروع",
                "هيكل المشروع",
            ]
        )

    async def handle(self, question: str, lowered: str) -> str:
        k = await self.tools.execute("get_project_overview", {})
        return f"المشروع: {k.get('project_name')} (v{k.get('version')})\nملفات Python: {k.get('structure', {}).get('python_files')}"


class MicroservicesHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "microservices",
                "microservice",
                "الخدمات المصغرة",
                "خدمات مصغرة",
                "عدد الخدمات",
                "خدمة مصغرة",
            ]
        )

    async def handle(self, question: str, lowered: str) -> str:
        k = await self.tools.execute("get_microservices_overview", {})
        total = int(k.get("total_services", 0))
        raw_services = k.get("services", [])
        services = [str(name) for name in raw_services] if isinstance(raw_services, list) else []
        if total == 0:
            return "لا توجد خدمات مصغرة معرفة حالياً."

        wants_names = any(
            token in lowered
            for token in ["ما هي", "اسم", "الأسماء", "قائمة", "list", "اسماء", "أسماء"]
        )
        summary = f"عدد الخدمات المصغرة: {total}."
        if wants_names:
            lines = "\n".join(f"- {name}" for name in services)
            return f"{summary}\nأسماء الخدمات:\n{lines}"
        return summary
