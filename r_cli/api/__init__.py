"""R CLI API - REST API daemon for R Agent Runtime."""

from r_cli.api.audit import (
    AuditAction,
    AuditEvent,
    AuditLogger,
    audit_log,
    get_audit_logger,
)
from r_cli.api.auth import (
    AuthResult,
    AuthStorage,
    Token,
    create_access_token,
    get_current_auth,
    require_auth,
    require_scopes,
)
from r_cli.api.permissions import (
    PermissionChecker,
    Scope,
    check_skill_permission,
)
from r_cli.api.rate_limit import (
    RateLimitConfig,
    RateLimiter,
    RateLimitMiddleware,
    get_rate_limiter,
)
from r_cli.api.server import create_app, run_server

__all__ = [
    "AuditAction",
    "AuditEvent",
    "AuditLogger",
    "AuthResult",
    "AuthStorage",
    "PermissionChecker",
    "RateLimitConfig",
    "RateLimitMiddleware",
    "RateLimiter",
    "Scope",
    "Token",
    "audit_log",
    "check_skill_permission",
    "create_access_token",
    "create_app",
    "get_audit_logger",
    "get_current_auth",
    "get_rate_limiter",
    "require_auth",
    "require_scopes",
    "run_server",
]
