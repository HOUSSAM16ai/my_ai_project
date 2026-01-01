"""
Unified Protocol Definitions for CS51 Abstraction System
تعريفات البروتوكولات الموحدة لنظام التجريد CS51

This module defines ALL protocols used across the system.
Centralized protocol definitions ensure consistency and prevent duplication.

Architecture Philosophy:
- Protocol-Oriented Programming (POP) over inheritance
- Composition over inheritance at every level
- Type-safe polymorphism through structural subtyping
- Zero coupling to concrete implementations

Based on latest research:
- Swift's Protocol-Oriented Programming (WWDC 2015+)
- Rust's Trait System
- Haskell's Type Classes
- Python PEP 544 (Structural Subtyping)
"""

from typing import TypeVar, Generic, Protocol, runtime_checkable, Any, Callable
from collections.abc import Sequence, Mapping, Awaitable
from datetime import datetime

T = TypeVar('T')
ID = TypeVar('ID')
Input = TypeVar('Input')
Output = TypeVar('Output')
State = TypeVar('State')

# ============================================================================
# Core System Protocols
# ============================================================================

@runtime_checkable
class Logger(Protocol):
    """
    Universal logging protocol.
    
    Abstracts logging so business logic never depends on concrete logger.
    """
    
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message."""
        ...
    
    def info(self, message: str, **context: Any) -> None:
        """Log info message."""
        ...
    
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message."""
        ...
    
    def error(self, message: str, **context: Any) -> None:
        """Log error message."""
        ...
    
    def critical(self, message: str, **context: Any) -> None:
        """Log critical message."""
        ...


@runtime_checkable
class AsyncLogger(Protocol):
    """
    Async logging protocol for non-blocking operations.
    """
    
    async def debug(self, message: str, **context: Any) -> None:
        """Log debug message asynchronously."""
        ...
    
    async def info(self, message: str, **context: Any) -> None:
        """Log info message asynchronously."""
        ...
    
    async def warning(self, message: str, **context: Any) -> None:
        """Log warning message asynchronously."""
        ...
    
    async def error(self, message: str, **context: Any) -> None:
        """Log error message asynchronously."""
        ...
    
    async def critical(self, message: str, **context: Any) -> None:
        """Log critical message asynchronously."""
        ...


@runtime_checkable
class Metrics(Protocol):
    """
    Metrics recording protocol.
    
    Abstracts metrics collection for observability.
    """
    
    def increment(self, name: str, value: float = 1.0, **tags: str) -> None:
        """Increment a counter metric."""
        ...
    
    def gauge(self, name: str, value: float, **tags: str) -> None:
        """Record a gauge metric."""
        ...
    
    def histogram(self, name: str, value: float, **tags: str) -> None:
        """Record a histogram metric."""
        ...
    
    def timing(self, name: str, duration_ms: float, **tags: str) -> None:
        """Record a timing metric."""
        ...


@runtime_checkable
class Cache(Protocol, Generic[T]):
    """
    Universal cache protocol.
    
    Abstracts caching mechanism.
    """
    
    async def get(self, key: str) -> T | None:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Set value in cache."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        ...


# ============================================================================
# Data Access Protocols
# ============================================================================

@runtime_checkable
class Readable(Protocol, Generic[T, ID]):
    """
    Protocol for reading entities.
    
    Minimum interface for read-only operations.
    """
    
    async def get(self, id: ID) -> T | None:
        """Get entity by ID."""
        ...
    
    async def list(self) -> Sequence[T]:
        """List all entities."""
        ...


@runtime_checkable
class Writable(Protocol, Generic[T]):
    """
    Protocol for writing entities.
    
    Minimum interface for write operations.
    """
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        ...
    
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        ...
    
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID."""
        ...


@runtime_checkable
class CRUD(Readable[T, ID], Writable[T], Protocol):
    """
    Complete CRUD protocol.
    
    Combines read and write operations.
    """
    pass


@runtime_checkable
class Queryable(Protocol, Generic[T]):
    """
    Protocol for complex queries.
    
    Enables filtering, sorting, pagination without breaking abstraction.
    """
    
    async def find(self, criteria: Mapping[str, Any]) -> Sequence[T]:
        """Find entities matching criteria."""
        ...
    
    async def find_one(self, criteria: Mapping[str, Any]) -> T | None:
        """Find single entity matching criteria."""
        ...
    
    async def count(self, criteria: Mapping[str, Any] | None = None) -> int:
        """Count entities matching criteria."""
        ...


# ============================================================================
# Service Protocols
# ============================================================================

@runtime_checkable
class Service(Protocol, Generic[Input, Output]):
    """
    Universal service protocol.
    
    Services encapsulate business operations.
    """
    
    async def execute(self, input: Input) -> Output:
        """Execute service operation."""
        ...


@runtime_checkable
class Validator(Protocol, Generic[T]):
    """
    Validation protocol.
    
    Abstracts validation logic.
    """
    
    def validate(self, value: T) -> list[str]:
        """
        Validate value.
        
        Returns:
            List of validation errors (empty if valid)
        """
        ...
    
    def is_valid(self, value: T) -> bool:
        """Check if value is valid."""
        ...


@runtime_checkable
class Transformer(Protocol, Generic[Input, Output]):
    """
    Transformation protocol.
    
    Abstracts data transformation.
    """
    
    def transform(self, input: Input) -> Output:
        """Transform input to output."""
        ...


@runtime_checkable
class AsyncTransformer(Protocol, Generic[Input, Output]):
    """
    Async transformation protocol.
    """
    
    async def transform(self, input: Input) -> Output:
        """Transform input to output asynchronously."""
        ...


# ============================================================================
# Notification Protocols
# ============================================================================

@runtime_checkable
class Notifier(Protocol):
    """
    Notification protocol.
    
    Abstracts notification mechanism.
    """
    
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        **metadata: Any
    ) -> bool:
        """
        Send notification.
        
        Args:
            recipient: Notification recipient
            subject: Notification subject
            body: Notification body
            **metadata: Additional metadata
            
        Returns:
            True if sent successfully
        """
        ...


@runtime_checkable
class EmailNotifier(Notifier, Protocol):
    """
    Email notification protocol.
    """
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Sequence[Any] | None = None
    ) -> bool:
        """Send email notification."""
        ...


@runtime_checkable
class PushNotifier(Notifier, Protocol):
    """
    Push notification protocol.
    """
    
    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Mapping[str, Any] | None = None
    ) -> bool:
        """Send push notification."""
        ...


# ============================================================================
# Security Protocols
# ============================================================================

@runtime_checkable
class Authenticator(Protocol):
    """
    Authentication protocol.
    
    Abstracts authentication mechanism.
    """
    
    async def authenticate(
        self,
        credentials: Mapping[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Authenticate user.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Tuple of (success, user_id or error_message)
        """
        ...


@runtime_checkable
class Authorizer(Protocol):
    """
    Authorization protocol.
    
    Abstracts authorization logic.
    """
    
    async def authorize(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user is authorized.
        
        Args:
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed
            
        Returns:
            True if authorized
        """
        ...


@runtime_checkable
class TokenGenerator(Protocol):
    """
    Token generation protocol.
    """
    
    def generate(self, payload: Mapping[str, Any], expires_in: int | None = None) -> str:
        """Generate token."""
        ...
    
    def verify(self, token: str) -> Mapping[str, Any] | None:
        """Verify and decode token."""
        ...


# ============================================================================
# Configuration Protocols
# ============================================================================

@runtime_checkable
class ConfigProvider(Protocol):
    """
    Configuration provider protocol.
    
    Abstracts configuration source.
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...
    
    def get_int(self, key: str, default: int | None = None) -> int | None:
        """Get integer configuration value."""
        ...
    
    def get_bool(self, key: str, default: bool | None = None) -> bool | None:
        """Get boolean configuration value."""
        ...
    
    def get_list(self, key: str, default: list | None = None) -> list:
        """Get list configuration value."""
        ...


# ============================================================================
# Serialization Protocols
# ============================================================================

@runtime_checkable
class Serializer(Protocol, Generic[T]):
    """
    Serialization protocol.
    
    Abstracts serialization format.
    """
    
    def serialize(self, obj: T) -> str | bytes:
        """Serialize object."""
        ...
    
    def deserialize(self, data: str | bytes) -> T:
        """Deserialize data."""
        ...


@runtime_checkable
class JSONSerializer(Serializer[T], Protocol):
    """JSON serialization protocol."""
    
    def to_json(self, obj: T) -> str:
        """Serialize to JSON string."""
        ...
    
    def from_json(self, json_str: str) -> T:
        """Deserialize from JSON string."""
        ...


# ============================================================================
# File System Protocols
# ============================================================================

@runtime_checkable
class FileReader(Protocol):
    """
    File reading protocol.
    """
    
    async def read(self, path: str) -> bytes:
        """Read file contents."""
        ...
    
    async def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read file as text."""
        ...
    
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        ...


@runtime_checkable
class FileWriter(Protocol):
    """
    File writing protocol.
    """
    
    async def write(self, path: str, content: bytes) -> None:
        """Write bytes to file."""
        ...
    
    async def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """Write text to file."""
        ...
    
    async def append(self, path: str, content: bytes) -> None:
        """Append bytes to file."""
        ...


# ============================================================================
# Network Protocols
# ============================================================================

@runtime_checkable
class HTTPClient(Protocol):
    """
    HTTP client protocol.
    """
    
    async def get(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None
    ) -> tuple[int, Mapping[str, str], bytes]:
        """
        Send GET request.
        
        Returns:
            Tuple of (status_code, headers, body)
        """
        ...
    
    async def post(
        self,
        url: str,
        data: bytes | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None
    ) -> tuple[int, Mapping[str, str], bytes]:
        """
        Send POST request.
        
        Returns:
            Tuple of (status_code, headers, body)
        """
        ...


# ============================================================================
# Event System Protocols
# ============================================================================

@runtime_checkable
class EventEmitter(Protocol, Generic[T]):
    """
    Event emitter protocol.
    """
    
    def emit(self, event: T) -> None:
        """Emit an event synchronously."""
        ...
    
    async def emit_async(self, event: T) -> None:
        """Emit an event asynchronously."""
        ...


@runtime_checkable
class EventListener(Protocol, Generic[T]):
    """
    Event listener protocol.
    """
    
    async def on_event(self, event: T) -> None:
        """Handle an event."""
        ...


# ============================================================================
# Time Protocols
# ============================================================================

@runtime_checkable
class Clock(Protocol):
    """
    Clock protocol for time abstraction.
    
    Enables testing with controlled time.
    """
    
    def now(self) -> datetime:
        """Get current datetime."""
        ...
    
    def timestamp(self) -> float:
        """Get current Unix timestamp."""
        ...


# ============================================================================
# Retry and Resilience Protocols
# ============================================================================

@runtime_checkable
class RetryPolicy(Protocol):
    """
    Retry policy protocol.
    """
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if operation should be retried."""
        ...
    
    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry."""
        ...


@runtime_checkable
class CircuitBreaker(Protocol):
    """
    Circuit breaker protocol for fault tolerance.
    """
    
    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """Execute function with circuit breaker protection."""
        ...
    
    def is_open(self) -> bool:
        """Check if circuit is open (blocking calls)."""
        ...
    
    def reset(self) -> None:
        """Reset circuit breaker."""
        ...


# ============================================================================
# Rate Limiting Protocols
# ============================================================================

@runtime_checkable
class RateLimiter(Protocol):
    """
    Rate limiter protocol.
    """
    
    async def acquire(self, key: str) -> bool:
        """
        Try to acquire rate limit permit.
        
        Args:
            key: Rate limit key (e.g., user ID, IP address)
            
        Returns:
            True if permit acquired, False if rate limited
        """
        ...
    
    async def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        ...


# ============================================================================
# ID Generation Protocols
# ============================================================================

@runtime_checkable
class IDGenerator(Protocol, Generic[ID]):
    """
    ID generation protocol.
    """
    
    def generate(self) -> ID:
        """Generate a new unique ID."""
        ...


@runtime_checkable
class UUIDGenerator(IDGenerator[str], Protocol):
    """
    UUID generation protocol.
    """
    
    def generate_uuid(self) -> str:
        """Generate a UUID string."""
        ...


# ============================================================================
# Health Check Protocols
# ============================================================================

@runtime_checkable
class HealthCheck(Protocol):
    """
    Health check protocol.
    """
    
    async def check(self) -> tuple[bool, str]:
        """
        Perform health check.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        ...


@runtime_checkable
class Pingable(Protocol):
    """
    Pingable protocol for connection testing.
    """
    
    async def ping(self) -> bool:
        """
        Ping to check connectivity.
        
        Returns:
            True if reachable
        """
        ...


# ============================================================================
# Export All Protocols
# ============================================================================

__all__ = [
    # Core system
    "Logger",
    "AsyncLogger",
    "Metrics",
    "Cache",
    
    # Data access
    "Readable",
    "Writable",
    "CRUD",
    "Queryable",
    
    # Services
    "Service",
    "Validator",
    "Transformer",
    "AsyncTransformer",
    
    # Notifications
    "Notifier",
    "EmailNotifier",
    "PushNotifier",
    
    # Security
    "Authenticator",
    "Authorizer",
    "TokenGenerator",
    
    # Configuration
    "ConfigProvider",
    
    # Serialization
    "Serializer",
    "JSONSerializer",
    
    # File system
    "FileReader",
    "FileWriter",
    
    # Network
    "HTTPClient",
    
    # Events
    "EventEmitter",
    "EventListener",
    
    # Time
    "Clock",
    
    # Resilience
    "RetryPolicy",
    "CircuitBreaker",
    "RateLimiter",
    
    # ID generation
    "IDGenerator",
    "UUIDGenerator",
    
    # Health
    "HealthCheck",
    "Pingable",
]
