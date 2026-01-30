import re

from app.services.chat.agents.admin_handlers.base import AdminCommandHandler


class CodeSearchHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "find",
                "locate",
                "search",
                "where",
                "file",
                "line",
                "أي ملف",
                "أين",
                "سطر",
                "ابحث",
            ]
        )

    async def handle(self, question: str, lowered: str) -> str:
        q = self._extract_search_query(question)
        if not q:
            return "حدد كلمة للبحث."
        gov = await self.refactor_agent.process({})
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"
        res = await self.tools.execute("search_codebase", {"query": q})
        return self._format_locs(res, f"نتائج '{q}'")

    def _extract_search_query(self, s: str) -> str | None:
        if q := self._extract_quoted(s):
            return q
        tokens = [t for t in re.sub(r"[؟?]", " ", s).split() if len(t) > 2]
        return tokens[-1] if tokens else None

    def _format_locs(self, results: list[dict], title: str) -> str:
        if not results:
            return f"{title}: لا توجد نتائج."
        lines = [
            f"- {result['file_path']}"
            + (f":{result['line_number']}" if result.get("line_number") else "")
            for result in results[:10]
        ]
        return f"{title}:\n" + "\n".join(lines)


class FileSnippetHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return ".py" in lowered and ("line" in lowered or "سطر" in lowered or ":" in lowered)

    async def handle(self, question: str, lowered: str) -> str:
        path, start, end = self._extract_file_line(question)
        if not path or start is None:
            return "حدد الملف والسطر (file.py:10)."

        snip = await self.tools.execute(
            "read_file_snippet",
            {"file_path": path, "start_line": start, "end_line": end},
        )
        lines = "\n".join(
            f"{snip['start_line'] + i}: {line}" for i, line in enumerate(snip["lines"])
        )
        return f"مقتطف {path}:\n{lines}"

    def _extract_file_line(self, s: str) -> tuple[str | None, int | None, int | None]:
        m = re.search(r"([\w\-/\.]+\.py)(?::(\d+)(?:-(\d+))?)?", s)
        if not m:
            return None, None, None
        path = m.group(1)
        start = int(m.group(2)) if m.group(2) else None
        end = int(m.group(3)) if m.group(3) else None
        return path, start, end


class RouteHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(x in lowered for x in ["route", "endpoint", "api path", "مسار", "نقطة نهاية"])

    async def handle(self, question: str, lowered: str) -> str:
        f = self._extract_route_fragment(question)
        if not f:
            return "يرجى تحديد جزء من المسار."
        res = await self.tools.execute("find_route", {"path_fragment": f})
        return self._format_locs(res, f"مسارات '{f}'")

    def _extract_route_fragment(self, s: str) -> str | None:
        if q := self._extract_quoted(s):
            return q
        m = re.search(r"/[\w\-_\/]+", s)
        return m.group(0) if m else None

    def _format_locs(self, results: list[dict], title: str) -> str:
        # Duplicated from CodeSearchHandler, could be in base but it's small
        if not results:
            return f"{title}: لا توجد نتائج."
        lines = [
            f"- {result['file_path']}"
            + (f":{result['line_number']}" if result.get("line_number") else "")
            for result in results[:10]
        ]
        return f"{title}:\n" + "\n".join(lines)


class SymbolHandler(AdminCommandHandler):
    async def can_handle(self, lowered: str) -> bool:
        return any(x in lowered for x in ["function", "class", "دالة", "كلاس", "class "])

    async def handle(self, question: str, lowered: str) -> str:
        s = self._extract_symbol(question)
        if not s:
            return "حدد الرمز."
        res = await self.tools.execute("find_symbol", {"symbol": s})
        return self._format_locs(res, f"تعريفات '{s}'")

    def _extract_symbol(self, s: str) -> str | None:
        m = re.search(r"(?:دالة|function|class|كلاس)\s+([\w_]+)", s, re.IGNORECASE)
        return m.group(1) if m else None

    def _format_locs(self, results: list[dict], title: str) -> str:
        if not results:
            return f"{title}: لا توجد نتائج."
        lines = [
            f"- {result['file_path']}"
            + (f":{result['line_number']}" if result.get("line_number") else "")
            for result in results[:10]
        ]
        return f"{title}:\n" + "\n".join(lines)
