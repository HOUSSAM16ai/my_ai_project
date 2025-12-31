# 🏗️ CogniForge DevContainer - Professional Edition

## نظام بيئة التطوير الاحترافي | Professional Development Environment System

**Version**: 2.0.0  
**Date**: 2025-12-31  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents | جدول المحتويات

1. [Overview | نظرة عامة](#overview)
2. [Architecture | المعمارية](#architecture)
3. [Quick Start | البدء السريع](#quick-start)
4. [Lifecycle Hooks | خطافات دورة الحياة](#lifecycle-hooks)
5. [Troubleshooting | استكشاف الأخطاء](#troubleshooting)
6. [Development | التطوير](#development)
7. [Testing | الاختبار](#testing)
8. [Performance | الأداء](#performance)

---

## 🎯 Overview | نظرة عامة

CogniForge DevContainer is a **production-grade development environment** built on:

- **SICP Principles**: Abstraction barriers, functional composition
- **CS50 Standards**: Strict typing, comprehensive documentation
- **Industry Best Practices**: Idempotency, health checks, observability

### Key Features | الميزات الرئيسية

✅ **Zero-Downtime Startup**: Non-blocking lifecycle hooks  
✅ **Health-Gated Launch**: Browser opens only when app is ready  
✅ **Idempotent Operations**: Safe to run multiple times  
✅ **Comprehensive Logging**: Every action is tracked  
✅ **Performance Optimized**: React production build, memory monitoring  
✅ **Self-Healing**: Automatic recovery from common failures  

---

## 🏛️ Architecture | المعمارية

### Abstraction Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: User Interface (IDE/Browser)                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Application Runtime (Uvicorn/FastAPI)             │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Container Lifecycle (DevContainer Hooks)          │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: System Foundation (Docker/OS)                     │
└─────────────────────────────────────────────────────────────┘
```

### Lifecycle State Machine

```
CREATED → CONFIGURED → STARTING → READY → ATTACHED
   ↓          ↓           ↓         ↓        ↓
onCreate   onCreate    onStart   Health   onAttach
(secrets)  (validate)  (async)   (check)  (display)
```

### Component Structure

```
.devcontainer/
├── lib/
│   └── lifecycle_core.sh      # Core library (abstraction layer)
├── tests/
│   └── test_lifecycle.sh      # Test suite
├── on-create.sh               # Fast configuration (< 5s)
├── on-start.sh                # Background launcher
├── on-attach.sh               # Status display
├── supervisor.sh              # Application lifecycle manager
├── healthcheck.sh             # Health verification utility
├── diagnostics.sh             # Troubleshooting tool
├── devcontainer.json          # Container configuration
└── ARCHITECTURE.md            # Detailed architecture docs
```

---

## 🚀 Quick Start | البدء السريع

### For GitHub Codespaces

1. **Open in Codespaces**
   ```
   Click "Code" → "Codespaces" → "Create codespace on main"
   ```

2. **Wait for Initialization** (30-45 seconds)
   - Container creation: 10-15s
   - Environment setup: 5-10s
   - Application startup: 15-20s

3. **Monitor Progress**
   ```bash
   tail -f .superhuman_bootstrap.log
   ```

4. **Access Application**
   - Wait for: "✅ Application is healthy and ready!"
   - Open: http://localhost:8000

### For Local Development

1. **Open in VS Code**
   ```bash
   code .
   ```

2. **Reopen in Container**
   - Command Palette (Ctrl+Shift+P)
   - "Dev Containers: Reopen in Container"

3. **Follow same monitoring steps as above**

---

## 🔄 Lifecycle Hooks | خطافات دورة الحياة

### postCreateCommand (on-create.sh)

**Purpose**: Fast environment configuration  
**Duration**: < 5 seconds  
**Idempotent**: ✅ Yes

**Responsibilities**:
- Generate `.env` from Codespaces secrets
- Validate configuration
- Initialize state directories

**Example**:
```bash
bash .devcontainer/on-create.sh
```

### postStartCommand (on-start.sh)

**Purpose**: Launch background supervisor  
**Duration**: < 1 second (non-blocking)  
**Idempotent**: ✅ Yes

**Responsibilities**:
- Start supervisor in background
- Exit immediately to unblock IDE
- Log to `.superhuman_bootstrap.log`

**Example**:
```bash
bash .devcontainer/on-start.sh
```

### Background Supervisor (supervisor.sh)

**Purpose**: Application lifecycle management  
**Duration**: 30-45 seconds  
**Idempotent**: ✅ Yes

**Responsibilities**:
1. System readiness check (2s)
2. Install dependencies (~10-15s)
3. Run database migrations (~5-10s)
4. Seed admin user (~2-5s)
5. Start Uvicorn server (~5-10s)
6. Health check verification (~5-10s)

**Example**:
```bash
bash .devcontainer/supervisor.sh
```

### postAttachCommand (on-attach.sh)

**Purpose**: Display status information  
**Duration**: < 1 second  
**Idempotent**: ✅ Yes

**Responsibilities**:
- Show application status
- Display useful commands
- Provide access information

**Example**:
```bash
bash .devcontainer/on-attach.sh
```

---

## 🔧 Troubleshooting | استكشاف الأخطاء

### Quick Diagnostics

```bash
# Check application health
bash .devcontainer/healthcheck.sh

# Run full diagnostics
bash .devcontainer/diagnostics.sh --full

# View logs
tail -f .superhuman_bootstrap.log

# Check processes
ps aux | grep uvicorn
```

### Common Issues

#### Issue: Application not starting

**Symptoms**:
- Port 8000 not listening
- Health check fails

**Solution**:
```bash
# Check logs for errors
tail -50 .superhuman_bootstrap.log

# Restart supervisor
pkill -f uvicorn
bash .devcontainer/supervisor.sh
```

#### Issue: Browser crashes

**Cause**: This should be fixed in v2.0  
**Verification**:
```bash
# Check only one Uvicorn instance
ps aux | grep uvicorn | grep -v grep | wc -l
# Should output: 1
```

#### Issue: Slow startup

**Symptoms**:
- Takes > 60 seconds to become ready

**Solution**:
```bash
# Check resource usage
bash .devcontainer/diagnostics.sh --full

# Verify dependencies are cached
pip list | wc -l
```

---

## 💻 Development | التطوير

### Core Library (lifecycle_core.sh)

The core library provides reusable functions following SICP principles:

```bash
# Load library
source .devcontainer/lib/lifecycle_core.sh

# Logging
lifecycle_info "Information message"
lifecycle_warn "Warning message"
lifecycle_error "Error message"

# State management
lifecycle_set_state "my_state" "value"
value=$(lifecycle_get_state "my_state")
lifecycle_has_state "my_state"  # Returns 0 if exists

# Locking
lifecycle_acquire_lock "my_lock" 30  # 30s timeout
# ... critical section ...
lifecycle_release_lock "my_lock"

# Health checks
lifecycle_check_port 8000
lifecycle_check_http "http://localhost:8000/health" 200
lifecycle_wait_for_http "http://localhost:8000/health" 30

# Idempotency
lifecycle_run_once "operation_id" command arg1 arg2
```

### Adding New Lifecycle Steps

1. **Edit supervisor.sh**
2. **Add new step function**
3. **Call in sequence**
4. **Update state tracking**

Example:
```bash
# In supervisor.sh
my_custom_step() {
    lifecycle_info "Running custom step..."
    
    if my_command; then
        lifecycle_info "✅ Custom step completed"
        return 0
    else
        lifecycle_error "Custom step failed"
        return 1
    fi
}

# In main sequence
if my_custom_step; then
    lifecycle_set_state "custom_step_completed" "$(date +%s)"
fi
```

---

## 🧪 Testing | الاختبار

### Run Test Suite

```bash
bash .devcontainer/tests/test_lifecycle.sh
```

### Test Coverage

- ✅ Core library functions
- ✅ State management
- ✅ Locking mechanism
- ✅ Health checks
- ✅ Script existence and permissions
- ✅ Utility scripts

### Writing New Tests

```bash
# In test_lifecycle.sh
test_suite_my_feature() {
    echo "Test Suite: My Feature"
    
    # Test: Something works
    assert_true "my_condition" "My condition should be true"
    
    # Test: Values match
    assert_equals "expected" "actual" "Values should match"
    
    # Test: File exists
    assert_file_exists "/path/to/file" "File should exist"
}
```

---

## ⚡ Performance | الأداء

### Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Container Ready | < 60s | ~45s |
| App Healthy | < 30s | ~25s |
| Browser Load | < 2s | ~1.5s |
| Memory Usage | < 100MB | ~80MB |
| Uvicorn Instances | 1 | 1 |

### Monitoring

```bash
# Check performance
bash .devcontainer/diagnostics.sh --full

# Monitor memory
watch -n 5 'free -h'

# Track startup time
time bash .devcontainer/supervisor.sh
```

### Frontend Performance

- ✅ React production build (70% smaller)
- ✅ Memoized components
- ✅ Performance monitoring
- ✅ Message limit (20 max)
- ✅ Content truncation (25k chars)

---

## 📊 State Management | إدارة الحالة

### State Files

Located in `.devcontainer/state/`:

- `container_created`: Timestamp of container creation
- `env_generated`: How .env was generated (codespaces/example)
- `config_validated`: Configuration validation status
- `dependencies_installed`: Dependency installation timestamp
- `migrations_completed`: Migration completion timestamp
- `admin_seeded`: Admin seeding timestamp
- `uvicorn_pid`: Uvicorn process ID
- `app_healthy`: Application health timestamp
- `app_ready`: Application readiness flag
- `supervisor_running`: Supervisor process ID

### Querying State

```bash
# Check if state exists
if lifecycle_has_state "app_ready"; then
    echo "Application is ready"
fi

# Get state value
pid=$(lifecycle_get_state "uvicorn_pid")
echo "Uvicorn PID: $pid"

# List all states
ls -lh .devcontainer/state/
```

---

## 🔒 Security | الأمان

### Secrets Management

- ✅ Secrets loaded from Codespaces environment
- ✅ Never logged or displayed
- ✅ Stored in `.env` with restricted permissions
- ✅ `.env` excluded from git

### Best Practices

1. **Never commit secrets** to version control
2. **Use Codespaces secrets** for sensitive data
3. **Rotate secrets regularly**
4. **Audit access logs**

---

## 📚 References | المراجع

- [DevContainers Specification](https://containers.dev/)
- [SICP - Structure and Interpretation of Computer Programs](https://mitpress.mit.edu/sites/default/files/sicp/index.html)
- [CS50 - Harvard's Introduction to Computer Science](https://cs50.harvard.edu/)
- [Twelve-Factor App](https://12factor.net/)

---

## 🤝 Contributing | المساهمة

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 📄 License | الترخيص

See [LICENSE](../LICENSE) for details.

---

## 👥 Authors | المؤلفون

**CogniForge Engineering Team**

- Architecture: SICP + CS50 Principles
- Implementation: Professional Standards
- Documentation: Bilingual (Arabic + English)

---

**Last Updated**: 2025-12-31  
**Version**: 2.0.0  
**Status**: ✅ Production Ready
