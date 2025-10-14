# 🚀 Code Formatting - Quick Reference

## One-Command Solutions

### Format Code (Recommended before commit)
```bash
./scripts/format_code.sh
```
✅ Auto-formats all Python files with Black and isort

### Check Formatting (No changes)
```bash
./scripts/check_formatting.sh
```
✅ Verifies formatting without modifying files

### Setup Pre-commit Hooks (One-time)
```bash
./scripts/setup_pre_commit.sh
```
✅ Installs hooks that auto-format before every commit

## Daily Workflow

```bash
# Make changes to code
vim app/models.py

# Auto-format before commit
./scripts/format_code.sh

# Commit (or let hooks do it automatically)
git add .
git commit -m "feat: add new model"
```

## If CI/CD Fails

```bash
# Option 1: Auto-fix
./scripts/format_code.sh
git add .
git commit -m "style: apply code formatting"
git push

# Option 2: Manual fix
black --line-length=100 app/ tests/
isort --profile=black --line-length=100 app/ tests/
git add .
git commit -m "style: fix formatting"
git push
```

## Pre-commit Hooks

### Enable (One-time)
```bash
./scripts/setup_pre_commit.sh
```

### Manual Run
```bash
pre-commit run --all-files
```

### Skip (Emergency only!)
```bash
git commit --no-verify -m "Emergency fix"
```

### Update Hooks
```bash
pre-commit autoupdate
```

## Manual Commands

### Black
```bash
# Format
black --line-length=100 app/ tests/

# Check only
black --check --diff --line-length=100 app/ tests/
```

### isort
```bash
# Sort imports
isort --profile=black --line-length=100 app/ tests/

# Check only
isort --check-only --diff --profile=black --line-length=100 app/ tests/
```

## Configuration Files

- **pyproject.toml** - Black & isort settings
- **.pre-commit-config.yaml** - Pre-commit hooks
- **.github/workflows/code-quality.yml** - CI/CD checks

## Documentation

📚 **[CODE_FORMATTING_GUIDE.md](CODE_FORMATTING_GUIDE.md)** - Complete guide

## Quick Tips

✅ **DO:**
- Run `./scripts/format_code.sh` before committing
- Install pre-commit hooks once per machine
- Let automation handle formatting

❌ **DON'T:**
- Format code manually
- Skip pre-commit hooks (unless emergency)
- Modify formatting config without team discussion

---

**Built with ❤️ by Houssam Benmerah**
