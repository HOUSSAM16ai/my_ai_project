# 🚀 Ultimate CI/CD Quick Reference

## 🎯 Quick Commands

```bash
# Test locally before pushing
./scripts/ci/test-locally.sh

# Auto-fix code issues
./scripts/ci/auto-fix.sh

# Format code
black --line-length=100 app/ tests/
isort --profile=black app/ tests/

# Run tests like CI
pytest -v --reruns 1 -n auto --cov=app
```

## 📊 Workflows at a Glance

| Workflow | File | Purpose | Runs On |
|----------|------|---------|---------|
| 🏆 Ultimate CI | `ultimate-ci.yml` | Main CI (build, test, lint, security) | PR, Push |
| 🔄 Auto-Rerun | `auto-rerun-transients.yml` | Auto-rerun transient failures | Workflow completion |
| 🔍 Lint Workflows | `lint-workflows.yml` | Validate YAML syntax | PR, Push (workflow changes) |
| 📊 Health Monitor | `health-monitor.yml` | Track CI/CD health | Every 6 hours, workflow completion |

## ✅ Quality Gates

### Required (Must Pass)
- ✅ Build & Test (Python 3.11, 3.12)
- ✅ Black formatting
- ✅ isort (import sorting)
- ✅ Ruff linting
- ✅ Security scan (Bandit ≤15 high)
- ✅ pytest (all tests pass)

### Optional (Informational)
- ℹ️ MyPy type checking
- ℹ️ Docker build & scan
- ℹ️ Advanced security scans

## 🔄 Auto-Rerun Triggers

Automatically reruns when detecting:
- Network errors (ECONNRESET, ETIMEDOUT)
- Rate limiting (429, 5xx)
- Download failures
- Timeout issues

## 📈 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Success Rate | ≥95% | 🟢 |
| Avg Duration | <15min | 🟢 |
| Test Coverage | ≥30% | 🟢 |
| Security (High) | ≤15 | 🟢 |

## 🛠️ Troubleshooting

### CI Fails Randomly
✅ Check if auto-rerun triggered
✅ Look for transient patterns in logs

### Tests Too Slow
✅ Use `pytest -n auto` for parallel execution
✅ Run subset: `pytest tests/unit/`

### Cache Not Working
✅ Check cache keys in workflow
✅ Use `skip_cache: true` in workflow_dispatch

## 📚 Documentation

- 📖 [Full Guide (EN)](ULTIMATE_CI_CD_SOLUTION.md)
- 📖 [Full Guide (AR)](ULTIMATE_CI_CD_SOLUTION_AR.md)
- 📖 [README](README.md)

## 🎓 Best Practices

1. ✅ Always run `./scripts/ci/test-locally.sh` before pushing
2. ✅ Use `./scripts/ci/auto-fix.sh` to fix formatting
3. ✅ Set timeouts on all jobs and steps
4. ✅ Make tests idempotent
5. ✅ Use lockfiles for dependencies

---

*Built with ❤️ by Houssam Benmerah*
