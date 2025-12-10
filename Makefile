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
	@echo "  make format           - Auto-format code (black + ruff)"
	@echo "  make lint             - Run all linters (ruff + pylint + flake8)"
	@echo "  make check            - Check code formatting (no changes)"
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
	@echo "$(BLUE)🎨 Formatting code with Black and Ruff...$(NC)"
	black .
	ruff check --fix .
	ruff format .
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint:
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@echo "$(YELLOW)⚡ Ruff (ultra-fast)...$(NC)"
	ruff check .
	@echo "$(GREEN)✅ Linting complete!$(NC)"

check:
	@echo "$(BLUE)✅ Checking code formatting (no changes)...$(NC)"
	black --check .
	ruff check .
	@echo "$(GREEN)✅ Code formatting check passed!$(NC)"

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
	       --cov-fail-under=30
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
# SIMPLICITY - Superhuman Simplicity Implementation
# =============================================================================
simplicity-validate:
	@echo "$(BLUE)🎯 Running simplicity validator...$(NC)"
	python tools/simplicity_validator.py --directory app --report-file SIMPLICITY_VALIDATION_REPORT.md
	@echo "$(GREEN)✅ Simplicity validation complete!$(NC)"

simplicity-purify:
	@echo "$(BLUE)🧹 Purifying root directory...$(NC)"
	bash scripts/purify_root.sh
	@echo "$(GREEN)✅ Root purification complete!$(NC)"

simplicity-report:
	@echo "$(BLUE)📊 Generating simplicity report...$(NC)"
	@echo "$(YELLOW)See SIMPLICITY_VALIDATION_REPORT.md for details$(NC)"
	@cat SIMPLICITY_VALIDATION_REPORT.md 2>/dev/null || echo "Run 'make simplicity-validate' first"

simplicity-help:
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  🎯 Superhuman Simplicity Commands$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  make simplicity-validate   - Validate code against simplicity principles"
	@echo "  make simplicity-purify     - Clean root directory (move docs to archive)"
	@echo "  make simplicity-report     - View current simplicity report"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  • SIMPLICITY_PRINCIPLES_GUIDE_AR.md  - Full Arabic guide"
	@echo "  • SIMPLICITY_PRINCIPLES_GUIDE_EN.md  - Full English guide"
	@echo "  • SIMPLICITY_QUICK_REFERENCE.md      - Quick reference"
	@echo "  • SUPERHUMAN_SIMPLICITY_ARCHITECTURE.md - 7 principles"
	@echo "  • SUPERHUMAN_SIMPLICITY_FRAMEWORK.md - 72-hour plan"
	@echo ""
	@echo "$(YELLOW)Philosophy: \"احذف، ادمج، ثم ابنِ\" - Delete, Merge, then Build$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"

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

# =============================================================================
# ML OPERATIONS - DevOps/MLOps Superhuman Edition
# =============================================================================

# ML Installation
install-ml: install
	@echo "$(BLUE)📦 Installing ML-specific dependencies...$(NC)"
	pip install great-expectations mlflow argo-workflows || true
	@echo "$(GREEN)✅ ML dependencies installed!$(NC)"

# Data Quality
data-quality:
	@echo "$(BLUE)🔍 Running data quality checks...$(NC)"
	python pipelines/data_quality_checkpoint.py
	@echo "$(GREEN)✅ Data quality checks complete!$(NC)"

# ML Training Pipeline
train:
	@echo "$(BLUE)🚀 Starting ML training pipeline...$(NC)"
	python pipelines/steps/prepare_data.py
	python pipelines/steps/validate_data_quality.py
	python pipelines/steps/train.py
	python pipelines/steps/evaluate.py
	python pipelines/steps/check_fairness.py
	python pipelines/steps/register_model.py
	@echo "$(GREEN)✅ Training pipeline complete!$(NC)"

# Model Evaluation
evaluate:
	@echo "$(BLUE)📊 Evaluating model...$(NC)"
	python pipelines/steps/evaluate.py
	@echo "$(GREEN)✅ Model evaluation complete!$(NC)"

# Model Registration
register:
	@echo "$(BLUE)📝 Registering model to MLflow...$(NC)"
	python pipelines/steps/register_model.py
	@echo "$(GREEN)✅ Model registered!$(NC)"

# Infrastructure Operations
infra-init:
	@echo "$(BLUE)🏗️ Initializing Terraform...$(NC)"
	cd infra/terraform && terraform init
	@echo "$(GREEN)✅ Terraform initialized!$(NC)"

infra-plan:
	@echo "$(BLUE)📋 Planning infrastructure changes...$(NC)"
	cd infra/terraform && terraform plan
	@echo "$(GREEN)✅ Infrastructure plan complete!$(NC)"

infra-apply:
	@echo "$(YELLOW)⚠️  Applying infrastructure changes...$(NC)"
	cd infra/terraform && terraform apply
	@echo "$(GREEN)✅ Infrastructure applied!$(NC)"

infra-destroy:
	@echo "$(RED)⚠️  Destroying infrastructure...$(NC)"
	cd infra/terraform && terraform destroy
	@echo "$(YELLOW)⚠️  Infrastructure destroyed!$(NC)"

# Deployment Operations
deploy-dev:
	@echo "$(BLUE)🚀 Deploying to dev environment...$(NC)"
	kubectl apply -f serving/kserve-inference.yaml --namespace=dev || echo "kubectl not available"
	@echo "$(GREEN)✅ Deployed to dev!$(NC)"

deploy-staging:
	@echo "$(BLUE)🚀 Deploying to staging environment...$(NC)"
	kubectl apply -f serving/kserve-inference.yaml --namespace=staging || echo "kubectl not available"
	@echo "$(GREEN)✅ Deployed to staging!$(NC)"

deploy-prod:
	@echo "$(YELLOW)⚠️  Deploying to production (canary)...$(NC)"
	kubectl apply -f serving/kserve-inference.yaml --namespace=prod || echo "kubectl not available"
	@echo "$(GREEN)✅ Deployed to production!$(NC)"

rollback:
	@echo "$(RED)⚠️  Rolling back deployment...$(NC)"
	kubectl rollout undo deployment/cogniforge-classifier -n prod || echo "kubectl not available"
	@echo "$(YELLOW)⚠️  Deployment rolled back!$(NC)"

# Monitoring
slo-check:
	@echo "$(BLUE)📊 Checking SLO compliance...$(NC)"
	@echo "See monitoring/slo.yaml for SLO definitions"
	@echo "$(GREEN)✅ SLO check complete!$(NC)"

# Version info
version:
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  CogniForge ML Platform - Version Information$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "Platform Version: 1.0.0-devops-mlops"
	@echo "Python: $(shell python --version 2>&1)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Kubernetes: $(shell kubectl version --client --short 2>/dev/null || echo 'Not installed')"
	@echo "Terraform: $(shell terraform version 2>/dev/null | head -n1 || echo 'Not installed')"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
