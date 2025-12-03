# 📖 Responsibility Separation - Migration Guide
# دليل الترحيل لفصل المسؤوليات

## 🎯 Overview

This guide helps developers migrate existing code to use the new centralized infrastructure modules.

---

## 🔄 Migration Patterns

### Pattern 1: AI Client Migration

#### Before (Old Pattern)
```python
# In app/services/my_service.py
from app.services.llm_client_service import get_llm_client

class MyService:
    def __init__(self):
        self.client = get_llm_client()
```

#### After (New Pattern - Option 1: Direct)
```python
# In app/services/my_service.py
from app.core.ai_client_factory import get_ai_client

class MyService:
    def __init__(self):
        self.client = get_ai_client()
```

#### After (New Pattern - Option 2: Keep compatibility)
```python
# In app/services/my_service.py
# llm_client_service now delegates to centralized factory
from app.services.llm_client_service import get_llm_client

class MyService:
    def __init__(self):
        self.client = get_llm_client()  # Still works!
```

**Recommendation:** Use Option 2 for existing code, Option 1 for new code.

---

### Pattern 2: Circuit Breaker Migration

#### Before (Old Pattern with Duplicate Implementation)
```python
# In app/services/my_service.py
from dataclasses import dataclass
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreaker:
    # ... 80 lines of duplicate code ...
    pass

class MyService:
    def __init__(self):
        self.breaker = CircuitBreaker(name="my-service")
```

#### After (New Pattern)
```python
# In app/services/my_service.py
from app.core.resilience import get_circuit_breaker

class MyService:
    def __init__(self):
        self.breaker = get_circuit_breaker("my-service")
    
    def do_something(self):
        if self.breaker.allow_request():
            try:
                result = self._make_call()
                self.breaker.record_success()
                return result
            except Exception as e:
                self.breaker.record_failure()
                raise
        else:
            raise CircuitOpenError("my-service")
```

#### Legacy Compatibility (can_execute method)
```python
# If your code uses can_execute() instead of allow_request()
can_execute, msg = self.breaker.can_execute()
if can_execute:
    # proceed
else:
    # handle circuit open
```

---

### Pattern 3: HTTP Client Migration

#### Before (Old Pattern)
```python
# In app/services/my_service.py
import httpx

class MyService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100)
        )
```

#### After (New Pattern)
```python
# In app/services/my_service.py
from app.core.http_client_factory import get_http_client

class MyService:
    def __init__(self):
        self.http_client = get_http_client(
            name="my-service",
            timeout=30.0,
            max_connections=100
        )
```

---

## 📝 Step-by-Step Migration

### Step 1: Identify Usage

Run the analysis script to find what needs migration:

```bash
python3 /tmp/analyze_responsibilities.py
```

This will show you:
- Files using AI clients
- Files with circuit breakers
- Files creating HTTP clients

### Step 2: Update Imports

Replace old imports with new centralized imports:

```python
# OLD
from app.services.llm_client_service import get_llm_client

# NEW (for new code)
from app.core.ai_client_factory import get_ai_client

# OR keep old import (it delegates to new factory)
from app.services.llm_client_service import get_llm_client  # Still works!
```

### Step 3: Update Circuit Breaker Usage

Remove local circuit breaker implementations:

```python
# Remove these (80+ lines each):
# - class CircuitState(Enum)
# - class CircuitBreakerConfig
# - class CircuitBreaker

# Add this import instead:
from app.core.resilience import get_circuit_breaker, CircuitBreakerConfig

# Update usage:
breaker = get_circuit_breaker("service-name")
```

### Step 4: Test

Run validation:

```bash
python3 /tmp/validate_refactoring.py
```

### Step 5: Clean Up

Remove duplicate code:
- Delete local CircuitBreaker classes
- Remove duplicate client creation logic
- Remove unused imports

---

## 🔍 Common Issues & Solutions

### Issue 1: "Module not found" error

**Problem:**
```python
ImportError: cannot import name 'get_circuit_breaker' from 'app.core.resilience'
```

**Solution:**
Make sure you're importing from the correct module:
```python
# Correct
from app.core.resilience import get_circuit_breaker

# NOT
from app.core.resilience.circuit_breaker import get_circuit_breaker  # Wrong!
```

### Issue 2: Circuit breaker method not found

**Problem:**
```python
AttributeError: 'CircuitBreaker' object has no attribute 'can_execute'
```

**Solution:**
Make sure you're using the updated version of circuit_breaker.py that includes the `can_execute()` compatibility method.

### Issue 3: Client cache not clearing

**Problem:**
Clients are cached and not updating when you change configuration.

**Solution:**
```python
from app.core.ai_client_factory import clear_ai_client_cache
clear_ai_client_cache()
```

Or disable caching:
```python
from app.core.ai_client_factory import get_ai_client
client = get_ai_client(use_cache=False)
```

---

## ✅ Verification Checklist

After migration, verify:

- [ ] All imports resolve correctly
- [ ] No circular import errors
- [ ] Circuit breakers work (allow_request, record_success/failure)
- [ ] AI clients are created successfully
- [ ] HTTP clients connect properly
- [ ] Legacy code still works (backward compatibility)
- [ ] Tests pass
- [ ] No duplicate code remains

---

## 📊 Migration Progress Tracker

### High Priority (Core Services)

- [x] `chat_orchestrator_service.py` - Circuit breaker migrated
- [x] `llm_client_service.py` - Delegates to centralized factory
- [ ] `ai_gateway.py` - Needs migration
- [ ] `admin_chat_boundary_service.py` - Needs migration

### Medium Priority (API Services)

- [ ] `api_gateway_service.py` - Has duplicate circuit breaker
- [ ] `api_gateway_chaos.py` - Has duplicate circuit breaker
- [ ] `distributed_resilience_service.py` - Needs HTTP client migration
- [ ] `api_developer_portal_service.py` - Needs HTTP client migration

### Low Priority (Support Services)

- [ ] `aiops_self_healing_service.py` - Has circuit breaker
- [ ] `deployment_orchestrator_service.py` - Has circuit breaker
- [ ] `chaos_engineering.py` - Has circuit breaker
- [ ] `service_mesh_integration.py` - Has circuit breaker

---

## 💡 Best Practices

### 1. Incremental Migration
Don't migrate everything at once. Start with one service, test thoroughly, then move to the next.

### 2. Use Centralized Names
When getting circuit breakers, use consistent names:
```python
# Good
breaker = get_circuit_breaker("user-service-api")

# Bad
breaker = get_circuit_breaker("users")
breaker2 = get_circuit_breaker("user_svc")
```

### 3. Configure Appropriately
Don't use default configs for production:
```python
from app.core.resilience import get_circuit_breaker, CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=10,  # More lenient for prod
    timeout=60.0,          # Longer recovery time
)
breaker = get_circuit_breaker("my-service", config)
```

### 4. Log Important Events
```python
import logging
logger = logging.getLogger(__name__)

breaker = get_circuit_breaker("my-service")
if not breaker.allow_request():
    logger.warning(f"Circuit breaker OPEN for my-service")
    # Handle gracefully
```

### 5. Monitor Circuit Breaker States
```python
from app.core.resilience import get_all_circuit_breaker_stats

stats = get_all_circuit_breaker_stats()
for name, stat in stats.items():
    if stat["state"] == "open":
        logger.error(f"Circuit {name} is OPEN!")
```

---

## 🧪 Testing Guide

### Unit Testing

```python
import pytest
from app.core.resilience import get_circuit_breaker, reset_all_circuit_breakers

@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset circuit breakers before each test"""
    reset_all_circuit_breakers()
    yield
    reset_all_circuit_breakers()

def test_my_service():
    breaker = get_circuit_breaker("test-service")
    assert breaker.allow_request() == True
```

### Integration Testing

```python
from app.core.ai_client_factory import get_ai_client, clear_ai_client_cache

def test_ai_client_integration():
    # Clear cache before test
    clear_ai_client_cache()
    
    # Get client
    client = get_ai_client()
    assert client is not None
    
    # Clean up
    clear_ai_client_cache()
```

---

## 📚 Additional Resources

### Documentation
- `RESPONSIBILITY_SEPARATION_ARCHITECTURE.md` - Complete architecture
- `RESPONSIBILITY_SEPARATION_IMPLEMENTATION.md` - Implementation details
- Module docstrings in each factory

### Code Examples
- `app/services/chat_orchestrator_service.py` - Migrated example
- `app/services/llm_client_service.py` - Delegation example
- `/tmp/test_centralized_modules.py` - Test examples

### Support
If you encounter issues:
1. Check this guide first
2. Review module docstrings
3. Check the validation script output
4. Consult the architecture documentation

---

**Last Updated:** 2025-12-03  
**Version:** 1.0.0  
**Status:** Active

**Happy Migrating! 🚀**
**ترحيل سعيد! 🚀**
