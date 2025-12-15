"""
حارس القياس الأمني - Security Telemetry Guard

Collects security-related metrics, events, and audit logs.
Integrates with observability systems for security monitoring.
"""
import time
from typing import Any
from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


class TelemetryGuard(BaseMiddleware):
    """
    Security Telemetry Guard

    Features:
    - Security event logging
    - Audit trail generation
    - Metrics collection
    - Threat intelligence gathering
    """
    name = 'TelemetryGuard'
    order = 5

    def _setup(self):
        """Initialize telemetry collections"""
        self.security_events: list[dict[str, Any]] = []
        self.audit_trail: list[dict[str, Any]] = []
        self.metrics: dict[str, int] = {'total_requests': 0,
            'blocked_requests': 0, 'suspicious_requests': 0,
            'authenticated_requests': 0}
        self.max_events = self.config.get('max_events', 1000)

    def process_request(self, ctx: RequestContext) ->MiddlewareResult:
        """
        Track security telemetry

        Args:
            ctx: Request context

        Returns:
            Always succeeds, just tracks data
        """
        self.metrics['total_requests'] += 1
        if ctx.user_id:
            self.metrics['authenticated_requests'] += 1
        audit_entry = {'timestamp': time.time(), 'request_id': ctx.
            request_id, 'method': ctx.method, 'path': ctx.path,
            'ip_address': ctx.ip_address, 'user_id': ctx.user_id,
            'trace_id': ctx.trace_id}
        self._add_audit_entry(audit_entry)
        ctx.add_metadata('security_start_time', time.time())
        return MiddlewareResult.success()

    def on_error(self, ctx: RequestContext, error: Exception):
        """
        Track security errors

        Args:
            ctx: Request context
            error: Exception that occurred
        """
        error_str = str(error).lower()
        if 'blocked' in error_str or 'forbidden' in error_str:
            self.metrics['blocked_requests'] += 1
        elif 'suspicious' in error_str or 'threat' in error_str:
            self.metrics['suspicious_requests'] += 1
        event = {'timestamp': time.time(), 'event_type': 'security_block',
            'request_id': ctx.request_id, 'path': ctx.path, 'ip_address':
            ctx.ip_address, 'user_id': ctx.user_id, 'error': str(error),
            'trace_id': ctx.trace_id}
        self._add_security_event(event)

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        """
        Track completion metrics

        Args:
            ctx: Request context
            result: Middleware result
        """
        start_time = ctx.get_metadata('security_start_time')
        if start_time:
            duration = time.time() - start_time
            ctx.add_metadata('security_duration', duration)

    def _add_security_event(self, event: dict[str, Any]):
        """Add security event with size limit"""
        self.security_events.append(event)
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]

    def _add_audit_entry(self, entry: dict[str, Any]):
        """Add audit entry with size limit"""
        self.audit_trail.append(entry)
        if len(self.audit_trail) > self.max_events:
            self.audit_trail = self.audit_trail[-self.max_events:]

    def get_recent_events(self, limit: int=100) ->list[dict[str, Any]]:
        """
        Get recent security events

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        return self.security_events[-limit:]

    def get_statistics(self) ->dict:
        """Return telemetry statistics"""
        stats = super().get_statistics()
        stats.update({'metrics': self.metrics.copy(),
            'security_events_count': len(self.security_events),
            'audit_entries_count': len(self.audit_trail), 'block_rate': 
            self.metrics['blocked_requests'] / self.metrics[
            'total_requests'] if self.metrics['total_requests'] > 0 else 0.0})
        return stats
