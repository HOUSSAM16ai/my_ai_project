# app/security/waf.py

import contextlib
import re
from re import Pattern
from typing import TypedDict

from fastapi import HTTPException, Request, status


class ThreatSignature(TypedDict):
    """نمط تهديد مضبوط الأنواع يتضمن الاسم والتعبير النمطي المطابق."""

    name: str
    pattern: Pattern[str]


class WebApplicationFirewall:
    """جدار حماية تطبيقات الويب مع فحص بسيط للتهديدات الشائعة."""

    def __init__(self):
        self.threat_signatures: list[ThreatSignature] = self._init_threat_signatures()

    def _init_threat_signatures(self) -> list[ThreatSignature]:
        """ينشئ قائمة بالتوقيعات المعتمدة للفحص السريع."""
        return [
            {
                'name': 'SQL_INJECTION',
                'pattern': re.compile(r"(union\s+select|--|;)", re.IGNORECASE),
            },
            {'name': 'XSS', 'pattern': re.compile(r"<script>", re.IGNORECASE)},
        ]

    async def check_request(self, request: Request) -> None:
        """يفحص معطيات الطلب بحثاً عن أنماط هجوم معروفة ويرفضها عند التطابق."""
        all_params = await self._extract_all_params(request)
        for param_value in all_params.values():
            for signature in self.threat_signatures:
                if signature['pattern'].search(param_value):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Potential {signature['name']} attack detected.",
                    )

    async def _extract_all_params(self, request: Request) -> dict[str, str]:
        """يجمع معطيات الطلب ويحولها إلى نصوص لضمان فحص متسق."""
        params: dict[str, str] = dict(request.query_params.items())
        if request.method in ["POST", "PUT"]:
            with contextlib.suppress(Exception):
                body = await request.json()
                if isinstance(body, dict):
                    for key, value in body.items():
                        params[str(key)] = str(value)
        return params


waf = WebApplicationFirewall()
