# app/security/waf.py
import re
from typing import Any

from fastapi import HTTPException, Request, status


class WebApplicationFirewall:
    def __init__(self):
        self.threat_signatures = self._init_threat_signatures()

    def _init_threat_signatures(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "SQL_INJECTION",
                "pattern": re.compile(r"(union\s+select|--|;)", re.IGNORECASE),
            },
            {"name": "XSS", "pattern": re.compile(r"<script>", re.IGNORECASE)},
        ]

    async def check_request(self, request: Request):
        all_params = await self._extract_all_params(request)
        for param_name, param_value in all_params.items():
            if not isinstance(param_value, str):
                continue
            for signature in self.threat_signatures:
                if signature["pattern"].search(param_value):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Potential {signature['name']} attack detected.",
                    )

    async def _extract_all_params(self, request: Request) -> dict[str, Any]:
        params = {}
        params.update(request.query_params)
        if request.method in ["POST", "PUT"]:
            try:
                params.update(await request.json())
            except Exception:
                pass
        return params


waf = WebApplicationFirewall()
