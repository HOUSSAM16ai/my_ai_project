# 🏗️ SUPERHUMAN REFACTORING ARCHITECTURE

## 📊 Current State Analysis

### Critical Issues Identified:
1. **High Cyclomatic Complexity**: Functions with CC > 20
2. **Large Files**: 700+ lines with mixed responsibilities
3. **Code Duplication**: Repeated patterns across services
4. **Tight Coupling**: Direct dependencies between layers
5. **Limited Testability**: Complex functions hard to unit test

### Top Complexity Hotspots:
```
1. tool() - CC: 25 (app/services/agent_tools/core.py)
2. summarize_for_prompt() - CC: 25 (app/overmind/planning/deep_indexer_v2/summary.py)
3. orchestrate() - CC: 24 (app/services/chat/service.py)
4. text_completion() - CC: 23 (app/services/maestro.py)
```

---

## 🎯 Target Architecture

### Design Principles:
1. **Single Responsibility Principle (SRP)**
2. **Dependency Inversion Principle (DIP)**
3. **Interface Segregation Principle (ISP)**
4. **Command Query Separation (CQS)**
5. **Strategy Pattern for Algorithms**

### Layered Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     API LAYER (FastAPI)                      │
│  - Request Validation                                        │
│  - Response Formatting                                       │
│  - Error Handling                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  - Use Cases / Commands                                      │
│  - Orchestration Logic                                       │
│  - Transaction Management                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                              │
│  - Business Logic                                            │
│  - Domain Models                                             │
│  - Domain Services                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│  - Database Access                                           │
│  - External APIs                                             │
│  - Caching                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Refactoring Strategy

### Phase 1: Extract Strategy Patterns

#### 1.1 Intent Detection Strategy
**Current**: Monolithic if-elif chains in orchestrate()
**Target**: Strategy pattern with pluggable handlers

```python
# app/services/chat/strategies/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class IntentHandler(ABC):
    @abstractmethod
    async def can_handle(self, intent: ChatIntent) -> bool:
        pass
    
    @abstractmethod
    async def handle(self, context: ChatContext) -> AsyncGenerator[str, None]:
        pass

# app/services/chat/strategies/file_read_handler.py
class FileReadHandler(IntentHandler):
    async def can_handle(self, intent: ChatIntent) -> bool:
        return intent == ChatIntent.FILE_READ
    
    async def handle(self, context: ChatContext) -> AsyncGenerator[str, None]:
        path = context.params.get("path", "")
        # Focused logic here
        yield f"Reading {path}..."
```

#### 1.2 Tool Registry Pattern
**Current**: Complex decorator with nested logic
**Target**: Builder pattern with fluent API

```python
# app/services/agent_tools/registry/builder.py
class ToolBuilder:
    def __init__(self, name: str):
        self._config = ToolConfig(name=name)
    
    def with_description(self, desc: str) -> 'ToolBuilder':
        self._config.description = desc
        return self
    
    def with_parameters(self, params: dict) -> 'ToolBuilder':
        self._config.parameters = params
        return self
    
    def with_category(self, category: str) -> 'ToolBuilder':
        self._config.category = category
        return self
    
    def build(self) -> Tool:
        return Tool(self._config)

# Usage:
tool = (ToolBuilder("read_file")
    .with_description("Read file contents")
    .with_parameters({"path": {"type": "string"}})
    .with_category("filesystem")
    .build())
```

#### 1.3 Retry Strategy Pattern
**Current**: Inline retry logic in text_completion()
**Target**: Configurable retry policies

```python
# app/core/resilience/retry_policy.py
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar('T')

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    max_backoff: float = 10.0
    
    async def execute(self, func: Callable[[], T]) -> T:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func()
            except Exception as e:
                if attempt == self.max_attempts:
                    raise
                await self._backoff(attempt)
    
    async def _backoff(self, attempt: int):
        delay = min(
            self.backoff_multiplier ** attempt,
            self.max_backoff
        )
        await asyncio.sleep(delay)
```

### Phase 2: Extract Command Pattern

#### 2.1 Chat Commands
```python
# app/services/chat/commands/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ChatCommand(ABC):
    user_id: int
    conversation_id: int
    question: str
    
    @abstractmethod
    async def execute(self) -> AsyncGenerator[str, None]:
        pass

# app/services/chat/commands/file_read_command.py
class FileReadCommand(ChatCommand):
    path: str
    
    async def execute(self) -> AsyncGenerator[str, None]:
        # Single responsibility: read file
        content = await self._read_file()
        yield f"```\n{content}\n```"
    
    async def _read_file(self) -> str:
        # Focused implementation
        pass
```

### Phase 3: Extract Service Layer

#### 3.1 Separate Concerns
```python
# app/services/chat/orchestrator.py
class ChatOrchestrator:
    def __init__(
        self,
        intent_detector: IntentDetector,
        handler_registry: HandlerRegistry,
        metrics: MetricsCollector
    ):
        self._intent_detector = intent_detector
        self._handlers = handler_registry
        self._metrics = metrics
    
    async def process(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        # Single responsibility: orchestration
        intent = await self._intent_detector.detect(request.question)
        handler = self._handlers.get_handler(intent)
        
        async for chunk in handler.handle(request):
            yield chunk
```

### Phase 4: Extract Validation Layer

#### 4.1 Input Validation
```python
# app/core/validation/validators.py
from abc import ABC, abstractmethod

class Validator(ABC):
    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        pass

class PathValidator(Validator):
    def validate(self, path: str) -> ValidationResult:
        if not path:
            return ValidationResult.error("Path cannot be empty")
        if ".." in path:
            return ValidationResult.error("Path traversal not allowed")
        return ValidationResult.success()

# app/core/validation/chain.py
class ValidationChain:
    def __init__(self):
        self._validators: list[Validator] = []
    
    def add(self, validator: Validator) -> 'ValidationChain':
        self._validators.append(validator)
        return self
    
    def validate(self, value: Any) -> ValidationResult:
        for validator in self._validators:
            result = validator.validate(value)
            if not result.is_valid:
                return result
        return ValidationResult.success()
```

---

## 🚀 Implementation Roadmap

### Week 1: Foundation
- [ ] Create base abstractions (Strategy, Command, Handler)
- [ ] Implement validation framework
- [ ] Setup retry policy infrastructure

### Week 2: Chat Service Refactoring
- [ ] Extract intent handlers
- [ ] Implement command pattern
- [ ] Refactor orchestrator

### Week 3: Tool Registry Refactoring
- [ ] Implement builder pattern
- [ ] Extract tool validators
- [ ] Simplify decorator logic

### Week 4: Maestro Service Refactoring
- [ ] Extract retry logic
- [ ] Implement strategy for LLM clients
- [ ] Add circuit breaker pattern

### Week 5: Testing & Documentation
- [ ] Unit tests for all new components
- [ ] Integration tests
- [ ] Update documentation

---

## 📈 Success Metrics

### Code Quality Targets:
- **Cyclomatic Complexity**: Average < 5, Max < 10
- **Function Length**: Average < 20 lines, Max < 50 lines
- **Test Coverage**: > 85%
- **Duplication**: < 3%

### Performance Targets:
- **Response Time**: < 200ms (p95)
- **Error Rate**: < 0.1%
- **Throughput**: > 1000 req/s

### Maintainability Targets:
- **Time to Add Feature**: < 2 hours
- **Time to Fix Bug**: < 1 hour
- **Onboarding Time**: < 1 day

---

## 🔒 Horizontal Scaling Patterns

### 1. Stateless Services
```python
# All services must be stateless
class StatelessService:
    def __init__(self, config: Config):
        # No mutable state
        self._config = config
    
    async def process(self, request: Request) -> Response:
        # Pure function - no side effects
        pass
```

### 2. Event-Driven Architecture
```python
# app/core/events/bus.py
class EventBus:
    async def publish(self, event: Event):
        # Async event publishing
        pass
    
    async def subscribe(self, event_type: str, handler: EventHandler):
        # Subscribe to events
        pass
```

### 3. Circuit Breaker Pattern
```python
# app/core/resilience/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self._failure_count = 0
        self._threshold = failure_threshold
        self._state = CircuitState.CLOSED
    
    async def call(self, func: Callable) -> Any:
        if self._state == CircuitState.OPEN:
            raise CircuitOpenError()
        
        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

### 4. Bulkhead Pattern
```python
# app/core/resilience/bulkhead.py
class Bulkhead:
    def __init__(self, max_concurrent: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute(self, func: Callable) -> Any:
        async with self._semaphore:
            return await func()
```

---

## 🎯 API-First Design

### 1. OpenAPI Specification
```yaml
# api_contracts/chat/v1/openapi.yaml
openapi: 3.0.0
info:
  title: Chat Service API
  version: 1.0.0
paths:
  /chat/stream:
    post:
      summary: Stream chat response
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatRequest'
      responses:
        '200':
          description: Streaming response
          content:
            text/event-stream:
              schema:
                type: string
```

### 2. Contract Testing
```python
# tests/contracts/test_chat_api.py
import pytest
from schemathesis import from_path

schema = from_path("api_contracts/chat/v1/openapi.yaml")

@schema.parametrize()
def test_chat_api_contract(case):
    response = case.call()
    case.validate_response(response)
```

---

## 🔍 Observability

### 1. Structured Logging
```python
# app/core/logging/structured.py
import structlog

logger = structlog.get_logger()

logger.info(
    "chat_request_processed",
    user_id=user_id,
    conversation_id=conversation_id,
    intent=intent.value,
    duration_ms=duration,
    tokens_used=tokens
)
```

### 2. Distributed Tracing
```python
# app/core/tracing/tracer.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_chat(request: ChatRequest):
    with tracer.start_as_current_span("process_chat") as span:
        span.set_attribute("user_id", request.user_id)
        span.set_attribute("intent", intent.value)
        # Process request
```

### 3. Metrics Collection
```python
# app/core/metrics/collector.py
from prometheus_client import Counter, Histogram

chat_requests = Counter(
    'chat_requests_total',
    'Total chat requests',
    ['intent', 'status']
)

chat_duration = Histogram(
    'chat_duration_seconds',
    'Chat request duration',
    ['intent']
)
```

---

## 📚 Documentation Strategy

### 1. Architecture Decision Records (ADRs)
```markdown
# ADR-001: Use Strategy Pattern for Intent Handlers

## Status
Accepted

## Context
Current if-elif chain in orchestrate() has CC of 24

## Decision
Implement Strategy pattern with pluggable handlers

## Consequences
- Reduced complexity
- Easier testing
- Better extensibility
```

### 2. API Documentation
- OpenAPI specs for all endpoints
- Example requests/responses
- Error codes and handling

### 3. Code Documentation
- Docstrings for public APIs
- Architecture diagrams
- Sequence diagrams for complex flows

---

## ✅ Verification Checklist

- [ ] All functions have CC < 10
- [ ] No file exceeds 300 lines
- [ ] Test coverage > 85%
- [ ] All APIs have OpenAPI specs
- [ ] Distributed tracing implemented
- [ ] Circuit breakers in place
- [ ] Horizontal scaling verified
- [ ] Documentation complete
