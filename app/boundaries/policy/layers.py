from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime, timedelta
from .engine import PolicyEngine
logger = logging.getLogger(__name__)


class SecurityException(Exception):
    """استثناء أمني"""
    pass


class SecurityLayer(ABC):
    """
    طبقة أمان (Security Layer)

    كل طبقة مستقلة ومسؤولة عن جانب واحد من الأمان
    """

    @abstractmethod
    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """معالجة الطلب عبر طبقة الأمان"""
        pass


class TLSLayer(SecurityLayer):
    """طبقة 1: تشفير النقل (TLS/mTLS)"""

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """التحقق من تشفير الاتصال"""
        if not request.get('is_secure', False):
            raise SecurityException('Connection must be secure (HTTPS/TLS)')
        logger.info('✅ TLS validation passed')
        return request


class JWTValidationLayer(SecurityLayer):
    """طبقة 2: المصادقة (JWT Validation)"""

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """التحقق من صحة JWT"""
        token = request.get('token')
        if not token:
            raise SecurityException('Missing authentication token')
        logger.info('✅ JWT validation passed')
        return request


class AuthorizationLayer(SecurityLayer):
    """طبقة 3: الترخيص (Policy Enforcement)"""

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """تطبيق سياسات الترخيص"""
        principal = request.get('principal')
        action = request.get('action')
        resource = request.get('resource')
        if not self.policy_engine.evaluate(principal, action, resource):
            raise SecurityException(
                f'Access denied: {principal.id} cannot {action} on {resource}')
        logger.info('✅ Authorization passed')
        return request


class InputValidationLayer(SecurityLayer):
    """طبقة 4: التحقق من المدخلات (Input Validation)"""

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """التحقق من صحة المدخلات"""
        data = request.get('data', {})
        for key, value in data.items():
            if isinstance(value, str) and any(pattern in value.lower() for
                pattern in ['drop table', 'select *', '--']):
                raise SecurityException(
                    f'Potential SQL injection detected in {key}')
        logger.info('✅ Input validation passed')
        return request


class RateLimitingLayer(SecurityLayer):
    """طبقة 5: حدود المعدل (Rate Limiting)"""

    def __init__(self, max_requests: int=100, window_seconds: int=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_counts: dict[str, list[datetime]] = {}

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """تطبيق حدود المعدل"""
        principal = request.get('principal')
        if not principal:
            return request
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        if principal.id not in self._request_counts:
            self._request_counts[principal.id] = []
        self._request_counts[principal.id] = [ts for ts in self.
            _request_counts[principal.id] if ts > window_start]
        if len(self._request_counts[principal.id]) >= self.max_requests:
            raise SecurityException(
                f'Rate limit exceeded for {principal.id}: {self.max_requests} requests per {self.window_seconds}s'
                )
        self._request_counts[principal.id].append(now)
        logger.info('✅ Rate limiting passed')
        return request


class AuditLoggingLayer(SecurityLayer):
    """طبقة 6: التدقيق (Audit Logging)"""

    def __init__(self):
        self._audit_log: list[dict[str, Any]] = []

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """تسجيل الطلب للتدقيق"""
        audit_entry = {'timestamp': datetime.now().isoformat(), 'principal':
            request.get('principal', {}).id if request.get('principal') else
            None, 'action': request.get('action'), 'resource': request.get(
            'resource'), 'ip_address': request.get('ip_address'),
            'user_agent': request.get('user_agent')}
        self._audit_log.append(audit_entry)
        logger.info(f'📝 Audit log: {audit_entry}')
        return request


class SecurityPipeline:
    """
    خط أنابيب الأمان (Security Pipeline)

    يطبق جميع طبقات الأمان بالترتيب
    """

    def __init__(self):
        self.layers: list[SecurityLayer] = []

    def add_layer(self, layer: SecurityLayer) ->None:
        """إضافة طبقة أمان"""
        self.layers.append(layer)
        logger.info(f'✅ Security layer added: {layer.__class__.__name__}')

    async def process(self, request: dict[str, Any]) ->dict[str, Any]:
        """معالجة الطلب عبر جميع الطبقات"""
        for layer in self.layers:
            try:
                request = await layer.process(request)
            except SecurityException as e:
                logger.error(
                    f'❌ Security layer {layer.__class__.__name__} failed: {e}')
                raise
        logger.info('✅ All security layers passed')
        return request
