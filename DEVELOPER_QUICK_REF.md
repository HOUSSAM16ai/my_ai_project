# ⚡ Developer Quick Reference - Code Quality

## 🚀 Essential Commands

### Installation (One-time)
```bash
make install-dev          # Install all dev tools
make install-pre-commit   # Setup git hooks
```

### Daily Workflow
```bash
make format              # Auto-format code
make lint                # Check code quality
make test                # Run tests
make quality             # Run ALL checks
```

### Before Committing
```bash
# These run automatically on commit:
make format              # Black + isort
make lint                # Ruff + Pylint + Flake8
make security            # Bandit + Safety

# Or run all at once:
make quality
```

## 📋 Quality Gates

| Check | Tool | Auto-fix | Required |
|-------|------|----------|----------|
| Format | Black | ✅ | 100% |
| Imports | isort | ✅ | 100% |
| Lint | Ruff | ⚠️ Partial | Pass |
| Type | MyPy | ❌ | Pass |
| Security | Bandit | ❌ | 0 critical |
| Coverage | pytest | ❌ | 80%+ |
| Complexity | Radon | ❌ | ≤15 |

## 🎯 Standards

### Code Style
- **Line length**: 100 characters
- **Indentation**: 4 spaces (Python), 2 spaces (YAML/JSON)
- **Quotes**: Double quotes preferred
- **Imports**: Sorted with isort (Google style)

### Type Hints
```python
def function_name(param: str, count: int = 0) -> bool:
    """Brief description.
    
    Args:
        param: Parameter description
        count: Count description
        
    Returns:
        True if successful
    """
    return True
```

### Docstrings
```python
class MyClass:
    """Brief class description.
    
    Longer description if needed.
    
    Attributes:
        attr_name: Attribute description
    """
    
    def method(self, param: str) -> None:
        """Brief method description.
        
        Args:
            param: Parameter description
        """
        pass
```

## 🔧 Tools Reference

### Black (Formatter)
```bash
black --line-length=100 app/
black --check app/          # Check only
black --diff app/           # Show changes
```

### Ruff (Linter)
```bash
ruff check app/             # Check
ruff check app/ --fix       # Auto-fix
ruff check app/ --statistics # Summary
```

### MyPy (Type Checker)
```bash
mypy app/                   # Check all
mypy app/models.py          # Check file
mypy --strict app/          # Strict mode
```

### Bandit (Security)
```bash
bandit -r app/              # Scan
bandit -r app/ -f json      # JSON report
bandit -r app/ -ll          # Low severity
```

### pytest (Testing)
```bash
pytest                      # Run all
pytest tests/test_file.py   # Run file
pytest -v                   # Verbose
pytest --cov=app            # With coverage
pytest -k test_name         # By name
pytest -m unit              # By marker
```

## 📊 Coverage Commands

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage
make coverage               # Opens HTML report

# Coverage with missing lines
pytest --cov=app --cov-report=term-missing
```

## 🐛 Debugging Failed Checks

### Black Failed
```bash
# See what will change
black --diff app/

# Apply fixes
make format
```

### Ruff Failed
```bash
# See issues
ruff check app/

# Auto-fix
ruff check app/ --fix

# Remaining issues
ruff check app/ --statistics
```

### MyPy Failed
```bash
# See type errors
mypy app/

# Ignore specific line
x = some_function()  # type: ignore

# Ignore imports
mypy app/ --ignore-missing-imports
```

### Tests Failed
```bash
# Verbose output
pytest -vv -s

# Single test
pytest tests/test_file.py::test_function

# Debug with pdb
pytest --pdb
```

## 🚨 Common Issues

### Import Errors
```python
# ❌ Wrong
from app.models import User, Task, Mission

# ✅ Correct (isort style)
from app.models import Mission, Task, User
```

### Line Too Long
```python
# ❌ Wrong
very_long_function_call(argument1, argument2, argument3, argument4, argument5)

# ✅ Correct
very_long_function_call(
    argument1,
    argument2,
    argument3,
    argument4,
    argument5,
)
```

### Type Hints
```python
# ❌ Wrong
def process(data):
    return data

# ✅ Correct
def process(data: dict[str, Any]) -> dict[str, Any]:
    return data
```

## 🔄 Pre-commit Hooks

### What Runs Automatically
1. ✅ Trim whitespace
2. ✅ Fix line endings
3. ✅ Check YAML/JSON
4. ✅ Format with Black
5. ✅ Sort imports (isort)
6. ✅ Lint with Ruff
7. ✅ Type check (MyPy)
8. ✅ Security scan (Bandit)
9. ✅ Detect secrets
10. ✅ Check file sizes

### Bypass Hooks (Emergency Only)
```bash
git commit --no-verify -m "message"
```

### Update Hooks
```bash
pre-commit autoupdate
make pre-commit-update
```

## 📈 CI/CD Pipeline

### GitHub Actions Jobs
1. **Lint & Format** - Code style
2. **Security Scan** - Vulnerabilities
3. **Type Check** - Type safety
4. **Complexity** - Maintainability
5. **Test Suite** - Coverage
6. **Quality Gate** - Final check

### Workflow Triggers
- Push to `main` or `develop`
- Pull requests
- Manual dispatch

## 🎯 Best Practices

### Commits
```bash
# Format before commit
make format

# Check quality
make lint

# Run tests
make test

# Then commit
git add .
git commit -m "feat: description"
```

### Pull Requests
1. ✅ All tests pass
2. ✅ Coverage ≥ 80%
3. ✅ No security issues
4. ✅ Code formatted
5. ✅ Types checked
6. ✅ Complexity OK

### Code Review Checklist
- [ ] Code formatted (Black)
- [ ] Imports sorted (isort)
- [ ] No linting errors (Ruff)
- [ ] Type hints added (MyPy)
- [ ] Tests added
- [ ] Coverage maintained
- [ ] Documentation updated
- [ ] No security issues

## 📚 More Info

- **Full Guide**: [CODE_QUALITY_GUIDE.md](CODE_QUALITY_GUIDE.md)
- **All Commands**: `make help`
- **Configuration**: [pyproject.toml](pyproject.toml)

---

**🏆 Standards**: Exceeding Google, Facebook, Microsoft, OpenAI, Apple  
**Built with ❤️ by Houssam Benmerah**
