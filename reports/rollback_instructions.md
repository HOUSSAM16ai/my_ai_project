# Rollback Instructions

If critical issues arise, follow these steps to revert to the pre-Phase-3 state.

## 1. Revert Code Changes
Execute the following git commands to reverse the commits:

```bash
# Revert Dockerfile changes
git checkout <PRE_PHASE_3_COMMIT_SHA> -- Dockerfile

# Revert Main Application Entrypoint
git checkout <PRE_PHASE_3_COMMIT_SHA> -- app/main.py

# Restore Middleware
git checkout <PRE_PHASE_3_COMMIT_SHA> -- app/middleware/error_response_factory.py
git checkout <PRE_PHASE_3_COMMIT_SHA> -- app/middleware/error_handler.py
```

## 2. Restore Legacy Files
Move files back from legacy storage:

```bash
mv legacy/flask/error_handler.py app/middleware/error_handler.py
mv legacy/flask/error_handler_v2.py app/middleware/error_handling/error_handler.py
rm -rf legacy/flask
```

## 3. Reinstall Dependencies
If `requirements.txt` was modified (it wasn't in this specific run, but if it were):

```bash
pip install -r requirements.txt
```

## 4. Verify Reversion
Run the baseline tests to ensure the old Flask application starts (if applicable).
```bash
python -m pytest tests/legacy_tests/
```
