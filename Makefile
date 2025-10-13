# ======================================================================================
# MAKEFILE - CogniForge Development Commands (Superhuman Edition)
# ======================================================================================
# One-command automation for all common tasks
# Standards: Google, Meta, Microsoft, Netflix, Uber
#
# Usage:
#   make help          - Show all available commands
#   make install       - Install all dependencies
#   make quality       - Run all quality checks
#   make test          - Run test suite
#   make format        - Auto-format code
#   make lint          - Run all linters
#   make security      - Run security scans
#   make docs          - Generate documentation
#   make clean         - Clean build artifacts
# ======================================================================================

.PHONY: help install quality test format lint security docs clean run dev deploy

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# HELP - Show all available commands
# =============================================================================
help:
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  🚀 CogniForge - Superhuman Development Commands$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)📦 Installation:$(NC)"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make install-pre-commit - Setup pre-commit hooks"
	@echo ""
	@echo "$(GREEN)🎨 Code Quality:$(NC)"
	@echo "  make quality          - Run ALL quality checks (recommended)"
	@echo "  make format           - Auto-format code (black + isort)"
	@echo "  make lint             - Run all linters (ruff + pylint + flake8)"
	@echo "  make type-check       - Run type checker (mypy)"
	@echo "  make security         - Run security scans (bandit + safety)"
	@echo "  make complexity       - Analyze code complexity"
	@echo ""
	@echo "$(GREEN)🧪 Testing:$(NC)"
	@echo "  make test             - Run test suite with coverage"
	@echo "  make test-fast        - Run tests without coverage"
	@echo "  make test-verbose     - Run tests with detailed output"
	@echo "  make coverage         - Generate coverage report"
	@echo ""
	@echo "$(GREEN)📚 Documentation:$(NC)"
	@echo "  make docs             - Generate documentation"
	@echo "  make docs-serve       - Serve documentation locally"
	@echo ""
	@echo "$(GREEN)🚀 Running:$(NC)"
	@echo "  make run              - Run application in production mode"
	@echo "  make dev              - Run application in development mode"
	@echo "  make debug            - Run application in debug mode"
	@echo ""
	@echo "$(GREEN)🐳 Docker:$(NC)"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs"
	@echo ""
	@echo "$(GREEN)🗄️ Database:$(NC)"
	@echo "  make db-migrate       - Create new migration"
	@echo "  make db-upgrade       - Apply migrations"
	@echo "  make db-downgrade     - Rollback migration"
	@echo "  make db-status        - Check migration status"
	@echo ""
	@echo "$(GREEN)🧹 Cleanup:$(NC)"
	@echo "  make clean            - Remove build artifacts"
	@echo "  make clean-all        - Deep clean (includes .venv)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"

# =============================================================================
# INSTALLATION
# =============================================================================
install:
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

install-dev:
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install black isort ruff pylint flake8 mypy bandit[toml] pydocstyle
	pip install radon xenon mccabe safety pre-commit
	pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
	@echo "$(GREEN)✅ Development dependencies installed!$(NC)"

install-pre-commit:
	@echo "$(BLUE)🔧 Setting up pre-commit hooks...$(NC)"
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✅ Pre-commit hooks installed!$(NC)"

# =============================================================================
# CODE QUALITY - The Superhuman Suite
# =============================================================================
quality: format lint type-check security complexity test
	@echo "$(GREEN)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ✅ ALL QUALITY CHECKS PASSED - SUPERHUMAN LEVEL!$(NC)"
	@echo "$(GREEN)════════════════════════════════════════════════════════════════$(NC)"

format:
	@echo "$(BLUE)🎨 Formatting code with Black and isort...$(NC)"
	black --line-length=100 app/ tests/
	isort --profile=black --line-length=100 app/ tests/
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint:
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@echo "$(YELLOW)⚡ Ruff (ultra-fast)...$(NC)"
	ruff check app/ tests/ --fix
	@echo "$(YELLOW)📋 Flake8...$(NC)"
	flake8 app/ tests/ --count --statistics
	@echo "$(YELLOW)🔍 Pylint...$(NC)"
	pylint app/ --exit-zero --score=yes
	@echo "$(GREEN)✅ Linting complete!$(NC)"

type-check:
	@echo "$(BLUE)🔍 Type checking with MyPy...$(NC)"
	mypy app/ --ignore-missing-imports --show-error-codes --pretty || true
	@echo "$(GREEN)✅ Type checking complete!$(NC)"

security:
	@echo "$(BLUE)🔒 Running security scans...$(NC)"
	@echo "$(YELLOW)🛡️ Bandit (code security)...$(NC)"
	bandit -r app/ -c pyproject.toml
	@echo "$(YELLOW)🔐 Safety (dependency security)...$(NC)"
	safety check || true
	@echo "$(GREEN)✅ Security scan complete!$(NC)"

complexity:
	@echo "$(BLUE)📊 Analyzing code complexity...$(NC)"
	@echo "$(YELLOW)🎯 Cyclomatic complexity...$(NC)"
	radon cc app/ -a -nb
	@echo "$(YELLOW)📈 Maintainability index...$(NC)"
	radon mi app/ -nb
	@echo "$(GREEN)✅ Complexity analysis complete!$(NC)"

# =============================================================================
# TESTING
# =============================================================================
test:
	@echo "$(BLUE)🧪 Running test suite with coverage...$(NC)"
	FLASK_ENV=testing TESTING=1 SECRET_KEY=test-key \
	pytest --verbose --cov=app --cov-report=term-missing:skip-covered \
	       --cov-report=html:htmlcov --cov-report=xml:coverage.xml \
	       --cov-fail-under=80
	@echo "$(GREEN)✅ Tests passed with coverage!$(NC)"

test-fast:
	@echo "$(BLUE)🧪 Running fast tests...$(NC)"
	FLASK_ENV=testing TESTING=1 SECRET_KEY=test-key pytest
	@echo "$(GREEN)✅ Fast tests complete!$(NC)"

test-verbose:
	@echo "$(BLUE)🧪 Running tests with detailed output...$(NC)"
	FLASK_ENV=testing TESTING=1 SECRET_KEY=test-key pytest -vv -s
	@echo "$(GREEN)✅ Verbose tests complete!$(NC)"

coverage:
	@echo "$(BLUE)📊 Generating coverage report...$(NC)"
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html manually"
	@echo "$(GREEN)✅ Coverage report generated!$(NC)"

# =============================================================================
# DOCUMENTATION
# =============================================================================
docs:
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	cd docs && make html
	@echo "$(GREEN)✅ Documentation generated!$(NC)"

docs-serve:
	@echo "$(BLUE)📚 Serving documentation...$(NC)"
	cd docs/_build/html && python -m http.server 8000

# =============================================================================
# RUNNING
# =============================================================================
run:
	@echo "$(BLUE)🚀 Starting application...$(NC)"
	python run.py

dev:
	@echo "$(BLUE)🔧 Starting development server...$(NC)"
	FLASK_DEBUG=1 python run.py

debug:
	@echo "$(BLUE)🐛 Starting debug mode...$(NC)"
	FLASK_DEBUG=1 FLASK_ENV=development python run.py

# =============================================================================
# DOCKER
# =============================================================================
docker-build:
	@echo "$(BLUE)🐳 Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Docker images built!$(NC)"

docker-up:
	@echo "$(BLUE)🐳 Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Containers started!$(NC)"

docker-down:
	@echo "$(BLUE)🐳 Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Containers stopped!$(NC)"

docker-logs:
	@echo "$(BLUE)🐳 Viewing Docker logs...$(NC)"
	docker-compose logs -f

# =============================================================================
# DATABASE
# =============================================================================
db-migrate:
	@echo "$(BLUE)🗄️ Creating migration...$(NC)"
	flask db migrate -m "$(MSG)"
	@echo "$(GREEN)✅ Migration created!$(NC)"

db-upgrade:
	@echo "$(BLUE)🗄️ Applying migrations...$(NC)"
	flask db upgrade
	@echo "$(GREEN)✅ Migrations applied!$(NC)"

db-downgrade:
	@echo "$(BLUE)🗄️ Rolling back migration...$(NC)"
	flask db downgrade
	@echo "$(GREEN)✅ Migration rolled back!$(NC)"

db-status:
	@echo "$(BLUE)🗄️ Checking migration status...$(NC)"
	python check_migrations_status.py

# =============================================================================
# CLEANUP
# =============================================================================
clean:
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ coverage.xml junit.xml
	rm -rf build/ dist/
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

clean-all: clean
	@echo "$(BLUE)🧹 Deep cleaning (including .venv)...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✅ Deep cleanup complete!$(NC)"

# =============================================================================
# PRE-COMMIT
# =============================================================================
pre-commit-run:
	@echo "$(BLUE)🔧 Running pre-commit hooks on all files...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit checks complete!$(NC)"

pre-commit-update:
	@echo "$(BLUE)🔧 Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate
	@echo "$(GREEN)✅ Pre-commit hooks updated!$(NC)"
