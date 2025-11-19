# MIGRATION ROLLBACK PLAN (STEP 2)

This document outlines the procedure for rolling back the changes made during the "Reality Kernel v2" migration (Step 2).

## Emergency Rollback Procedure

If the migration causes critical failures in staging or production, follow these steps to revert to the previous state.

### 1. Revert Git Branch

The simplest and most effective way to roll back is to revert the code to the state before the `step2/reality-kernel-v2-ultimate` branch was merged.

```bash
# Checkout the main branch
git checkout main

# Revert the merge commit of the Step 2 branch
# (You will need to find the specific merge commit hash)
git revert -m 1 <MERGE_COMMIT_HASH>
```

### 2. Manual File-by-File Rollback

If a full revert is not possible, you can manually roll back the changes on a per-service basis.

**For each migrated service (e.g., `history_service`):**

1.  **Restore from Backup:** During the migration, a `.bak` file was created for each modified service. To roll back, simply restore the original file:
    ```bash
    # Example for history_service
    mv app/services/history_service.py.bak app/services/history_service.py
    ```

2.  **Remove New Files:** Delete any new files that were created as part of the migration, including:
    *   The `app/core/kernel_v2` directory.
    *   The `migration/auto_loop` directory.
    *   The `tests/transcendent_v2` directory.

3.  **Clean up `requirements.txt`:** Remove any new dependencies that were added during the migration, such as `python-json-logger` and `aiosqlite`.

### 3. Database Considerations

The initial migration does not involve database schema changes. Therefore, no database rollback is required.

---
**IMPORTANT:** Always test the rollback procedure in a staging environment before applying it to production.
