from app.services.chat.agents.admin_handlers.base import AdminCommandHandler


class UserCountHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "how many users",
                "count users",
                "عدد المستخدمين",
                "كم مستخدم",
                "عدد الحسابات",
            ]
        )

    async def handle(self, question: str, lowered: str) -> str:
        gov = await self.data_agent.process(
            {"entity": "user", "operation": "count", "access_method": "service_api"}
        )
        if not gov.success:
            return f"Governance Error: {gov.message}"

        count = await self.tools.execute("get_user_count", {})
        if count == 0:
            return "لا يوجد مستخدمون مسجلون حالياً. (0 users)"
        return f"عدد المستخدمين الحاليين: {count}. ({count} users)"


class UserListHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered for x in ["list users", "all users", "قائمة المستخدمين", "عرض المستخدمين"]
        )

    async def handle(self, question: str, lowered: str) -> str:
        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "list",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        limit = self._extract_limit(lowered) or 20
        users = await self.tools.execute("list_users", {"limit": limit, "offset": 0})
        if not users:
            return "لا يوجد مستخدمون."

        lines = []
        for user in users:
            lines.append(
                f"- #{user['id']} | {user['full_name']} | {user['email']} | {user['status']}"
            )
        return "قائمة المستخدمين:\n" + "\n".join(lines)


class UserProfileHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(x in lowered for x in ["user profile", "تفاصيل المستخدم", "معلومات المستخدم"])

    async def handle(self, question: str, lowered: str) -> str:
        user_id = self._extract_id(question)
        if not user_id:
            return "يرجى تزويدي بمعرّف المستخدم (ID)."

        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "profile",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        profile = await self.tools.execute("get_user_profile", {"user_id": user_id})
        if profile.get("error"):
            return f"تعذر العثور على المستخدم #{user_id}."

        basic = profile.get("basic", {})
        stats = profile.get("statistics", {})
        return (
            f"ملف المستخدم #{user_id}:\n"
            f"- الاسم: {basic.get('full_name')}\n"
            f"- البريد: {basic.get('email')}\n"
            f"- الحالة: {basic.get('status')}\n"
            f"- الرسائل: {stats.get('total_chat_messages')}\n"
            f"- آخر نشاط: {stats.get('last_activity')}"
        )


class UserStatsHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in ["user stats", "user statistics", "إحصائيات المستخدم", "دردشات المستخدم"]
        )

    async def handle(self, question: str, lowered: str) -> str:
        user_id = self._extract_id(question)
        if not user_id:
            return "يرجى تحديد رقم المستخدم."

        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "statistics",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        stats = await self.tools.execute("get_user_statistics", {"user_id": user_id})
        if not stats:
            return f"لا توجد إحصائيات للمستخدم #{user_id}."

        return (
            f"إحصائيات #{user_id}:\n"
            f"- المهام: {stats.get('total_missions')} (مكتملة: {stats.get('completed_missions')})\n"
            f"- الرسائل: {stats.get('total_chat_messages')}"
        )
