# Contributing to CogniForge

## 🎯 Welcome!

Thank you for considering contributing to CogniForge! This document provides guidelines for contributing to the project while maintaining our **SUPERHUMAN** quality standards.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Quality Standards](#quality-standards)
5. [Pull Request Process](#pull-request-process)
6. [Coding Guidelines](#coding-guidelines)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation Guidelines](#documentation-guidelines)
9. [Security Guidelines](#security-guidelines)

---

## 📜 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please:

- ✅ Be respectful and inclusive
- ✅ Be collaborative and constructive
- ✅ Focus on what is best for the community
- ✅ Show empathy towards other community members
- ❌ Use inappropriate language or imagery
- ❌ Harass or discriminate against others
- ❌ Publish others' private information

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Git
- PostgreSQL (or use Supabase)
- Basic understanding of FastAPI and SQLAlchemy

### Initial Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/my_ai_project.git
   cd my_ai_project
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   make install-dev
   # Or manually:
   pip install -r requirements.txt
   pip install black isort ruff pylint flake8 mypy bandit[toml] pytest
   ```

4. **Setup Pre-Commit Hooks**
   ```bash
   make install-pre-commit
   # Or manually:
   ./scripts/setup_pre_commit.sh
   ```

5. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run Tests**
   ```bash
   make test
   ```

---

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/bug-description
```

**Branch Naming Convention**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, readable code
- Follow our coding guidelines (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Auto-format code
./scripts/format_all.sh

# Run all quality checks
./scripts/verify_quality.sh

# Run tests
make test

# Run security scan
./scripts/security_scan.sh
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "type: Brief description"
```

**Commit Message Format**:
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `security`: Security fixes

**Example**:
```
feat: Add user authentication system

Implement OAuth2 authentication with JWT tokens.
Includes user registration, login, and token refresh.

Closes #123
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub.

---

## ✨ Quality Standards

### Required Checks (Must Pass)

- ✅ **Black Formatting**: All code must be formatted with Black
- ✅ **Import Sorting**: Imports must be sorted with isort
- ✅ **Linting**: No Ruff or Flake8 errors
- ✅ **Security**: Bandit scan must pass (≤15 high severity issues)
- ✅ **Tests**: All tests must pass
- ✅ **Coverage**: Test coverage must not decrease

### Informational Checks

- 📊 **Type Checking**: MyPy (progressive, not blocking)
- 📊 **Complexity**: Radon/Xenon (monitored, not blocking)
- 📊 **Pylint Score**: Target 8.0+/10.0

### Running Quality Checks Locally

```bash
# One command to check everything
make quality

# Or use individual commands
make format        # Auto-format code
make lint          # Run linters
make type-check    # Run type checker
make security      # Run security scans
make test          # Run tests with coverage
```

---

## 🔀 Pull Request Process

### Before Creating a PR

1. ✅ All tests pass
2. ✅ Code is formatted (Black + isort)
3. ✅ No linting errors
4. ✅ Security scan passes
5. ✅ Documentation updated
6. ✅ CHANGELOG updated (if applicable)

### PR Title Format

```
<type>: <description>
```

Example: `feat: Add API rate limiting`

### PR Description Template

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code formatted (Black + isort)
- [ ] Linting passes (Ruff + Flake8)
- [ ] Security scan passes (Bandit)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG updated

## Related Issues
Closes #XXX

## Screenshots (if applicable)
[Add screenshots here]
```

### Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one approval required
3. **Manual Testing**: Reviewer tests the changes
4. **Final Approval**: Maintainer approves and merges

---

## 💻 Coding Guidelines

### Python Style (PEP 8 + Our Additions)

```python
# Use descriptive variable names
user_id = 123  # Good
uid = 123      # Avoid

# Maximum line length: 100 characters
def some_function(param1: str, param2: int) -> dict[str, object]:
    """Function docstring in Google style."""
    pass

# Use type hints
def process_data(data: list[dict]) -> dict[str, int]:
    """Process data and return counts."""
    return {"total": len(data)}

# Add docstrings to all public functions/classes
class MyClass:
    """Brief class description.
    
    Detailed class description if needed.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
    
    def public_method(self, param: str) -> None:
        """Brief method description.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value
            
        Raises:
            ValueError: When param is invalid
        """
        pass
```

### Code Organization

```
app/
├── __init__.py           # Application factory
├── models.py             # Database models
├── routes.py             # Route handlers
├── services/             # Business logic
│   ├── __init__.py
│   └── user_service.py
├── api/                  # API endpoints
│   ├── __init__.py
│   └── v1/
├── middleware/           # Middleware functions
├── utils/                # Utility functions
└── validators/           # Input validation
```

### Best Practices

- ✅ Use dependency injection
- ✅ Follow SOLID principles
- ✅ Keep functions small and focused
- ✅ Avoid deep nesting (max 3-4 levels)
- ✅ Use early returns to reduce complexity
- ✅ Handle errors explicitly
- ❌ No hardcoded values
- ❌ No commented-out code
- ❌ No debug print statements

---

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/test_user_service.py
import pytest
from app.services.user_service import UserService


class TestUserService:
    """Tests for UserService."""
    
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        # Arrange
        service = UserService(db_session)
        user_data = {"email": "test@example.com", "name": "Test User"}
        
        # Act
        user = service.create_user(user_data)
        
        # Assert
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_create_user_duplicate_email(self, db_session):
        """Test user creation with duplicate email fails."""
        # Arrange
        service = UserService(db_session)
        user_data = {"email": "test@example.com", "name": "Test User"}
        service.create_user(user_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already exists"):
            service.create_user(user_data)
```

### Test Coverage Requirements

- **Minimum**: 30% (enforced by CI)
- **Target**: 80%
- **New Code**: Must have tests

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_user_service.py

# Run with verbose output
pytest -vv

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## 📚 Documentation Guidelines

### Code Documentation

- ✅ Add docstrings to all public functions/classes
- ✅ Use Google-style docstrings
- ✅ Include examples in docstrings for complex functions
- ✅ Keep documentation up-to-date with code changes

### Project Documentation

- ✅ Update README.md for major features
- ✅ Add guides for new functionality
- ✅ Include screenshots for UI changes
- ✅ Create ADRs for architectural decisions

---

## 🔒 Security Guidelines

### Security Best Practices

- ✅ Never commit secrets or API keys
- ✅ Use environment variables for configuration
- ✅ Validate and sanitize all user input
- ✅ Use parameterized queries (SQLAlchemy handles this)
- ✅ Implement proper authentication and authorization
- ✅ Use HTTPS in production
- ✅ Keep dependencies updated

### Security Scanning

```bash
# Run security scan
./scripts/security_scan.sh

# Check for secrets
./scripts/security_scan.sh --secrets

# Check dependencies
./scripts/security_scan.sh --deps
```

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email: security@cogniforge.ai (or create a private security advisory)

---

## 🎓 Additional Resources

### Internal Documentation
- [Quality System Guide](QUALITY_SYSTEM_SUPERHUMAN.md)
- [Setup Guide](SETUP_GUIDE.md)
- [API Documentation](API_GATEWAY_COMPLETE_GUIDE.md)
- [Database Guide](DATABASE_GUIDE_AR.md)

### External Resources
- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## ❓ Getting Help

### Community Support
- **Discussions**: GitHub Discussions
- **Issues**: GitHub Issues (for bugs and features)
- **Chat**: Discord/Slack (if available)

### Maintainers
- **Houssam Benmerah** - Project Lead

---

## 🙏 Thank You!

Thank you for contributing to CogniForge! Every contribution, no matter how small, helps make this project better.

**Happy Coding! 🚀**

---

*Last Updated: 2025-11-01*
