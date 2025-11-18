# CLI Guidelines

This document provides guidelines for developing and using the CLI tool.

## Guiding Principles

- **No Flask Imports**: CLI handlers in `app/cli_handlers` must not import `current_app` or any other Flask-specific context variables. This ensures that the CLI is decoupled from the web application.
- **Transactional Sessions**: All database operations must be performed within a transactional session using the `transactional_session` context manager. This ensures that operations are atomic and can be safely rolled back in case of errors.
- **Safety Flags**: Critical commands must include safety flags like `--confirm` and `--dry-run` to prevent accidental data loss or modification in production environments.
- **Idempotency**: Strive to make commands idempotent where possible. This means that running the same command multiple times should produce the same result as running it once.

## Running Smoke Tests Locally

To run the smoke tests for the CLI layer, use the following command:

```bash
pytest tests/test_cli_smoke.py
```

## Runbook for Production Migrations

### Before Migration

1. **Backup the database**: Before applying any migrations to a production database, ensure you have a recent backup.
2. **Test in a staging environment**: Test the migration thoroughly in a staging environment that is as similar to production as possible.
3. **Notify users of planned maintenance**: If the migration is expected to cause downtime, notify users in advance.

### During Migration

1. **Put the application in maintenance mode**: This will prevent users from accessing the application while the migration is in progress.
2. **Run the migration command**:

   ```bash
   python -m app.cli db-migrate
   ```

### After Migration

1. **Verify the migration**: Manually check the database to ensure that the schema changes have been applied correctly.
2. **Disable maintenance mode**: Once you have verified that the migration was successful, disable maintenance mode.

## Rollback Procedure

In case a migration fails, follow these steps to roll back to the previous version:

1. **Identify the previous revision**: Use `alembic history` to find the revision hash of the previous migration.
2. **Downgrade the database**:

   ```bash
   alembic downgrade <previous_revision>
   ```

3. **Restore from backup**: If the downgrade fails, restore the database from the backup you created before the migration.
