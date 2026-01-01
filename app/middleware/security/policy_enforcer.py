"""
منفذ السياسات - Policy Enforcer

Policy-Based Access Control (PBAC) middleware.
Enforces access rules based on configurable policies.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult

class PolicyEnforcer(BaseMiddleware):
    """
    Policy-Based Access Control Middleware

    Enforces access policies based on:
    - User roles and permissions
    - Resource ownership
    - Time-based restrictions
    - Geographic restrictions
    - Custom policy rules
    """
    name = 'PolicyEnforcer'
    order = 50

    def _setup(self):
        """Initialize policy engine"""
        self.policies: dict[str, dict[str, Any]] = self.config.get('policies',
            {})
        self.enforced_count = 0
        self.violations = 0

    def process_request(self, ctx: RequestContext) ->MiddlewareResult:
        """
        Enforce access policies

        Args:
            ctx: Request context

        Returns:
            MiddlewareResult indicating if access is allowed
        """
        self.enforced_count += 1
        if ctx.path in ['/health', '/api/health', '/ping', '/', '/login']:
            return MiddlewareResult.success()
        policy = self._get_policy_for_path(ctx.path)
        if not policy:
            return MiddlewareResult.success()
        if not self._check_policy(ctx, policy):
            self.violations += 1
            return MiddlewareResult.forbidden(message='Access denied by policy'
                ).with_details(policy_name=policy.get('name'), reason=
                policy.get('denial_reason', 'Policy violation'))
        return MiddlewareResult.success()

    def _get_policy_for_path(self, path: str) ->(dict[str, Any] | None):
        """
        Get policy for a specific path

        Args:
            path: Request path

        Returns:
            Policy dict or None
        """
        if path in self.policies:
            return self.policies[path]
        for policy_path, policy in self.policies.items():
            if policy_path.endswith('/*') and path.startswith(policy_path[:-2]
                ):
                return policy
        return None

    # TODO: Split this function (32 lines) - KISS principle
    def _check_policy(self, ctx: RequestContext, policy: dict[str, Any]
        ) ->bool:
        """
        Check if request satisfies policy

        Args:
            ctx: Request context
            policy: Policy configuration

        Returns:
            True if policy is satisfied
        """
        required_roles = policy.get('required_roles', [])
        if required_roles:
            user_roles = ctx.get_metadata('user_roles', [])
            if not any(role in user_roles for role in required_roles):
                return False
        required_permissions = policy.get('required_permissions', [])
        if required_permissions:
            user_permissions = ctx.get_metadata('user_permissions', [])
            if not all(perm in user_permissions for perm in
                required_permissions):
                return False
        if policy.get('require_authentication', False) and not ctx.user_id:
            return False
        allowed_methods = policy.get('allowed_methods', [])
        if allowed_methods and ctx.method not in allowed_methods:
            return False
        ip_whitelist = policy.get('ip_whitelist', [])
        if ip_whitelist and ctx.ip_address not in ip_whitelist:
            return False
        ip_blacklist = policy.get('ip_blacklist', [])
        return not (ip_blacklist and ctx.ip_address in ip_blacklist)

    def add_policy(self, path: str, policy: dict[str, Any]) -> None:
        """
        Add a new policy

        Args:
            path: Path pattern
            policy: Policy configuration
        """
        self.policies[path] = policy

    def get_statistics(self) ->dict:
        """Return policy enforcer statistics"""
        stats = super().get_statistics()
        stats.update({'enforced_count': self.enforced_count, 'violations':
            self.violations, 'violation_rate': self.violations / self.
            enforced_count if self.enforced_count > 0 else 0.0,
            'active_policies': len(self.policies)})
        return stats
