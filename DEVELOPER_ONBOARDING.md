# 🚀 Developer Onboarding Checklist - CogniForge

Welcome to the CogniForge team! This checklist will help you get up and running quickly with our **SUPERHUMAN** quality standards.

---

## 📋 Before You Start

- [ ] Read [README.md](README.md) - Project overview
- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [ ] Read [QUALITY_SYSTEM_SUPERHUMAN.md](QUALITY_SYSTEM_SUPERHUMAN.md) - Quality standards

---

## 🔧 Environment Setup

### 1. Prerequisites Installation

- [ ] Install Python 3.12+ ([Download](https://www.python.org/downloads/))
- [ ] Install Git ([Download](https://git-scm.com/downloads))
- [ ] Install a code editor (VS Code, PyCharm, etc.)
- [ ] (Optional) Install Docker ([Download](https://www.docker.com/products/docker-desktop))

### 2. Repository Setup

```bash
# Fork and clone repository
- [ ] Fork repository on GitHub
- [ ] Clone your fork locally
      git clone https://github.com/YOUR_USERNAME/my_ai_project.git
      cd my_ai_project

# Create virtual environment
- [ ] Create Python virtual environment
      python -m venv .venv
- [ ] Activate virtual environment
      # Linux/Mac:
      source .venv/bin/activate
      # Windows:
      .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all development dependencies
- [ ] Install project dependencies
      make install-dev
      # Or manually:
      pip install -r requirements.txt
      pip install black isort ruff pylint flake8 mypy bandit pytest

# Setup pre-commit hooks
- [ ] Install pre-commit hooks
      make install-pre-commit
      # Or manually:
      ./scripts/setup_pre_commit.sh
```

### 4. Configure Environment

```bash
# Setup environment variables
- [ ] Copy .env.example to .env
      cp .env.example .env

- [ ] Edit .env with your configuration
      # Required variables:
      # - DATABASE_URL (use Supabase or local PostgreSQL)
      # - OPENROUTER_API_KEY (for AI features)
      # - SECRET_KEY (generate random string)

# Optional: Setup Supabase (recommended)
- [ ] Create Supabase account (free tier available)
- [ ] Create new project
- [ ] Copy connection string to DATABASE_URL
- [ ] Follow SUPABASE_SETUP_GUIDE.md
```

### 5. Verify Installation

```bash
# Run tests to verify setup
- [ ] Run test suite
      make test

# Check code quality tools
- [ ] Verify Black formatting
      black --check app/ tests/

- [ ] Verify isort
      isort --check-only app/ tests/

- [ ] Verify Ruff linting
      ruff check app/ tests/

# All checks should pass ✅
```

---

## 📚 Learn the Codebase

### Project Structure

- [ ] Understand the directory structure:
      ```
      app/
      ├── __init__.py        # Application factory
      ├── models.py          # Database models
      ├── routes.py          # Main routes
      ├── services/          # Business logic
      ├── api/               # API endpoints
      ├── middleware/        # Request/response middleware
      └── templates/         # Jinja2 templates
      ```

### Key Concepts

- [ ] Read [DATABASE_GUIDE_AR.md](DATABASE_GUIDE_AR.md) - Database architecture
- [ ] Read [API_GATEWAY_COMPLETE_GUIDE.md](API_GATEWAY_COMPLETE_GUIDE.md) - API design
- [ ] Explore [OVERMIND_README_v14.md](OVERMIND_README_v14.md) - AI orchestration
- [ ] Review [docs/adr/](docs/adr/) - Architecture decisions

### Run the Application

```bash
# Development mode
- [ ] Start the application
      make dev
      # Or:
      FLASK_DEBUG=1 python run.py

- [ ] Access the application
      Open browser: http://localhost:5000

- [ ] Explore the admin panel
      Navigate to: http://localhost:5000/admin
```

---

## 🎯 Development Workflow

### Daily Workflow

1. **Before Starting Work**
   - [ ] Pull latest changes: `git pull origin main`
   - [ ] Update dependencies: `pip install -r requirements.txt`
   - [ ] Run tests to ensure baseline: `make test`

2. **During Development**
   - [ ] Create feature branch: `git checkout -b feature/your-feature`
   - [ ] Make small, focused commits
   - [ ] Write tests for new code
   - [ ] Run quality checks frequently: `./scripts/verify_quality.sh --fast`

3. **Before Committing**
   - [ ] Format code: `./scripts/format_all.sh`
   - [ ] Run all quality checks: `make quality`
   - [ ] Run tests: `make test`
   - [ ] Review changes: `git diff`

4. **Creating Pull Request**
   - [ ] Push branch: `git push origin feature/your-feature`
   - [ ] Create PR on GitHub
   - [ ] Fill out PR template completely
   - [ ] Wait for CI/CD checks to pass
   - [ ] Request code review

### Quality Checklist (Before Every Commit)

```bash
# Auto-format code
- [ ] ./scripts/format_all.sh

# Verify formatting
- [ ] ./scripts/format_all.sh --check

# Run quality checks
- [ ] ./scripts/verify_quality.sh --fast

# Run tests
- [ ] make test

# Check security (periodic)
- [ ] ./scripts/security_scan.sh
```

---

## 🛠️ Essential Tools & Commands

### Quick Reference

```bash
# One-command quality check
make quality

# Format all code
make format

# Run all tests
make test

# Run security scan
./scripts/security_scan.sh

# View quality metrics
python scripts/quality_metrics.py

# Setup pre-commit hooks
make install-pre-commit
```

### Code Quality Standards

- [ ] **Line Length**: Maximum 100 characters
- [ ] **Formatting**: Use Black and isort
- [ ] **Linting**: Pass Ruff and Flake8
- [ ] **Type Hints**: Add type hints to new functions
- [ ] **Docstrings**: Google-style docstrings for public APIs
- [ ] **Tests**: Write tests for all new features
- [ ] **Coverage**: Maintain or improve test coverage

### Git Commit Messages

- [ ] Follow conventional commits format:
      ```
      <type>: <description>
      
      [optional body]
      
      [optional footer]
      ```

- [ ] Use these types:
      - `feat`: New feature
      - `fix`: Bug fix
      - `docs`: Documentation changes
      - `style`: Code style changes
      - `refactor`: Code refactoring
      - `test`: Test additions/changes
      - `chore`: Maintenance tasks

---

## 🔒 Security Best Practices

### Must Do

- [ ] **Never commit secrets** - Use environment variables
- [ ] **Validate input** - Always sanitize user input
- [ ] **Use parameterized queries** - SQLAlchemy handles this
- [ ] **Implement authentication** - For protected routes
- [ ] **Use HTTPS** - In production

### Security Scanning

```bash
# Run security scan
- [ ] ./scripts/security_scan.sh

# Check for secrets
- [ ] ./scripts/security_scan.sh --secrets

# Check dependencies
- [ ] ./scripts/security_scan.sh --deps
```

---

## 📊 Monitoring & Metrics

### Quality Metrics Dashboard

```bash
# View current metrics
- [ ] python scripts/quality_metrics.py

# Export metrics
- [ ] python scripts/quality_metrics.py --json > metrics.json
```

### Coverage Reports

```bash
# Generate coverage report
- [ ] make test
- [ ] open htmlcov/index.html
```

---

## 🆘 Getting Help

### Resources

- [ ] **Documentation**: Check [docs/](docs/) directory
- [ ] **Issues**: Search existing GitHub issues
- [ ] **Discussions**: GitHub Discussions for questions
- [ ] **Code Review**: Ask maintainers for guidance

### Common Issues

1. **Tests Failing**
   - Check DATABASE_URL is set correctly
   - Ensure all dependencies installed
   - Run: `FLASK_ENV=testing TESTING=1 pytest -vv`

2. **Import Errors**
   - Activate virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Formatting Issues**
   - Run auto-formatter: `./scripts/format_all.sh`
   - Check pre-commit hooks: `pre-commit run --all-files`

---

## ✅ Onboarding Complete!

Once you've checked off all items above, you're ready to contribute!

### Next Steps

1. **Pick Your First Issue**
   - [ ] Look for issues labeled `good-first-issue`
   - [ ] Comment on the issue to claim it
   - [ ] Ask questions if anything is unclear

2. **Make Your First Contribution**
   - [ ] Create a feature branch
   - [ ] Implement the change
   - [ ] Write tests
   - [ ] Submit a PR

3. **Join the Community**
   - [ ] Introduce yourself in Discussions
   - [ ] Star the repository ⭐
   - [ ] Share your experience

---

## 🎉 Welcome to the Team!

Thank you for joining CogniForge! We're excited to have you on board.

**Remember**: Quality over speed. Take time to understand the codebase and follow our **SUPERHUMAN** standards.

Happy coding! 🚀

---

*Questions? Create a discussion or reach out to maintainers.*
*Last Updated: 2025-11-01*
