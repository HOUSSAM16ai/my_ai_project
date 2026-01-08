# Refactor Baseline

## Canonical Commands Identified
- Tests: `make test`
- Lint: `make lint`
- Formatting check: `make check`
- Type check: `make type-check`
- Migrations: `make db-upgrade`

## Baseline Run (Phase 0)

### Lint
- Command: `make lint`
- Result: **failed** (ruff reported 3420 errors; includes unsorted imports and whitespace issues).

### Type Check
- Command: `make type-check`
- Result: **failed** (mypy reported numerous missing annotations and type mismatches).

### Tests
- Command: `make test`
- Result: **failed** (pytest rejected `--cov` arguments; coverage plugin not available).

### Formatting Check
- Command: `make check`
- Result: **failed** (black reports 531 files would be reformatted).

### Migrations
- Command: `make db-upgrade`
- Result: **passed** (alembic migrations applied with default SQLite fallback).

## Notes
- These failures will be addressed incrementally during the refactor plan execution.
- Any changes to the baseline outcomes will be recorded after each slice.
