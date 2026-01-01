# app/security/waf.py
import contextlib
import re

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

    async def check_request(self, request: Request) -> None:
        all_params = await self._extract_all_params(request)
        for _param_name, param_value in all_params.items():
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
            with contextlib.suppress(Exception):
                params.update(await request.json())
        return params

waf = WebApplicationFirewall()
