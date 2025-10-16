# 🚀 GitHub Actions - Quick Fix Reference

## 🎯 TL;DR - Quick Commands

```bash
# ✅ Run this single script to verify everything before pushing
bash scripts/verify_all_workflows.sh

# Expected output: "🎉 ALL CHECKS PASSED! WORKFLOWS WILL RUN SUCCESSFULLY!"
```

---

## 📋 If Workflows Fail - Quick Fixes

### ❌ Code Formatting (Black) Failed

**Error:** `Black formatting check failed!`

**Fix:**
```bash
black --line-length=100 app/ tests/
```

---

### ❌ Import Sorting (isort) Failed

**Error:** `Import sorting check failed!`

**Fix:**
```bash
isort --profile=black --line-length=100 app/ tests/
```

---

### ❌ Linting (Ruff) Failed

**Error:** `Ruff found X issues`

**Fix:**
```bash
ruff check --fix app/ tests/
```

---

### ❌ Tests Failed

**Error:** `Tests failed or timed out!`

**Fix:**
```bash
# Run tests locally to see what's failing
FLASK_ENV=testing TESTING=1 SECRET_KEY=test-secret \
pytest --verbose --tb=short -x

# Fix the failing tests, then run full suite
FLASK_ENV=testing TESTING=1 SECRET_KEY=test-secret \
pytest --cov=app --cov-report=xml
```

---

### ❌ Security (Bandit) Failed

**Error:** `Too many high severity security issues`

**Fix:**
```bash
# See specific issues
bandit -r app/ -c pyproject.toml

# Fix critical issues or add #nosec with justification
# For false positives: add comment like:
# password = get_password()  # nosec B105 - not a hardcoded password
```

---

## 🔧 One-Command Fix All

```bash
#!/bin/bash
# Auto-fix all common issues

# 1. Format code
black --line-length=100 app/ tests/
isort --profile=black --line-length=100 app/ tests/

# 2. Fix linting
ruff check --fix app/ tests/

# 3. Run tests
FLASK_ENV=testing TESTING=1 SECRET_KEY=test-secret \
pytest --verbose --cov=app --cov-report=xml

echo "✅ All fixes applied! Run 'git add .' and 'git commit' to save changes."
```

Save as `scripts/quick_fix.sh` and run:
```bash
chmod +x scripts/quick_fix.sh
bash scripts/quick_fix.sh
```

---

## 📊 Workflow Status Check

### Check Current Workflow Status

1. Go to GitHub repository
2. Click "Actions" tab
3. Look for workflows:
   - ✅ Green checkmark = Passing
   - ❌ Red X = Failed
   - 🟡 Yellow circle = Running

### View Specific Failure

1. Click on the failed workflow run
2. Click on the failed job
3. Expand the failed step
4. Read error message
5. Apply fix from this guide

---

## 🎯 Common Scenarios

### Scenario 1: "Black formatting check failed"

```bash
# Quick fix
black --line-length=100 app/ tests/
git add .
git commit -m "fix: Apply Black formatting"
git push
```

### Scenario 2: "Import sorting check failed"

```bash
# Quick fix
isort --profile=black --line-length=100 app/ tests/
git add .
git commit -m "fix: Fix import sorting"
git push
```

### Scenario 3: "Ruff linting failed"

```bash
# Quick fix
ruff check --fix app/ tests/
git add .
git commit -m "fix: Auto-fix Ruff linting issues"
git push
```

### Scenario 4: "Tests failed"

```bash
# Identify failing test
FLASK_ENV=testing TESTING=1 SECRET_KEY=test-secret pytest -x --tb=short

# Fix the test or code
# Then verify
FLASK_ENV=testing TESTING=1 SECRET_KEY=test-secret pytest

git add .
git commit -m "fix: Fix failing tests"
git push
```

### Scenario 5: "All workflows failing with same error"

This usually means a dependency issue or configuration problem.

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify locally
bash scripts/verify_all_workflows.sh

# If passes locally, push
git push
```

---

## 🏆 Best Practices

### Before Every Push

```bash
# Always run this before pushing
bash scripts/verify_all_workflows.sh
```

### Set Up Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Now formatting/linting runs automatically on commit!
```

### Add to .git/hooks/pre-push (Optional)

```bash
#!/bin/bash
# File: .git/hooks/pre-push

echo "🔍 Running pre-push checks..."

if bash scripts/verify_all_workflows.sh; then
    echo "✅ All checks passed! Pushing..."
    exit 0
else
    echo "❌ Checks failed! Fix issues before pushing."
    echo "Run: bash scripts/verify_all_workflows.sh"
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-push
```

---

## 📚 Detailed Documentation

For comprehensive information, see:

1. **GITHUB_ACTIONS_FIX_COMPLETE_FINAL.md** - Complete English documentation
2. **GITHUB_ACTIONS_الحل_النهائي_AR.md** - Complete Arabic documentation
3. **scripts/verify_all_workflows.sh** - Verification script

---

## 🆘 Emergency Fixes

### If Workflows Still Fail After All Fixes

1. **Check GitHub Actions status**
   ```
   https://www.githubstatus.com/
   ```

2. **Re-run failed workflows**
   - Go to Actions tab
   - Click on failed run
   - Click "Re-run all jobs"

3. **Check for dependency conflicts**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

4. **Clear cache and retry**
   - Go to Actions tab → Caches
   - Delete all caches
   - Re-run workflows

5. **Last resort: Force success (NOT recommended)**
   ```yaml
   # Only if you're absolutely sure the code is correct
   - name: Force success
     if: failure()
     run: exit 0
   ```

---

## ✅ Success Checklist

Before marking as complete:

- [ ] All tests pass locally (`pytest`)
- [ ] Black formatting passes (`black --check`)
- [ ] isort passes (`isort --check-only`)
- [ ] Ruff linting passes (`ruff check`)
- [ ] Security scan acceptable (`bandit -r app/`)
- [ ] Verification script passes (`bash scripts/verify_all_workflows.sh`)
- [ ] All workflows show green checkmarks on GitHub

---

## 🎉 Final Result

When everything is working:

```
════════════════════════════════════════════════════════════
  🏆 SUPERHUMAN CODE QUALITY ACHIEVED!
════════════════════════════════════════════════════════════

  ✅ Code Style & Formatting
  ✅ Security & Vulnerability Scanning
  ✅ Type Safety (Progressive)
  ✅ Code Complexity & Maintainability
  ✅ Test Coverage (Progressive 30% → 80%)

════════════════════════════════════════════════════════════
  🚀 DEPLOYMENT READY!
════════════════════════════════════════════════════════════
```

---

**Built with ❤️ by Houssam Benmerah**  
**CogniForge - Technology Surpassing All Tech Giants!**

---

**Quick Access:**
- 📖 Full Docs: `GITHUB_ACTIONS_FIX_COMPLETE_FINAL.md`
- 🔧 Verify Script: `bash scripts/verify_all_workflows.sh`
- 💡 This Guide: `GITHUB_ACTIONS_QUICK_FIX.md`
