# Rollback Instructions

In the event of a critical failure after deployment, follow these steps to rollback to the previous Flask-based version.

## Immediate Rollback (Docker/K8s)

1.  **Revert Image Tag**:
    Update your Kubernetes deployment or Docker Compose to use the previous image tag (e.g., `myapp:v1.0-flask` instead of `myapp:phase4-fastapi`).

    ```bash
    # Example for Docker Compose
    # Edit docker-compose.yml to point to previous image
    docker-compose up -d --force-recreate
    ```

2.  **Verify Rollback**:
    Check the logs to ensure Gunicorn (Flask) is starting up instead of Uvicorn.
    ```bash
    docker logs myapp
    # Should see: [INFO] Starting gunicorn...
    ```

## Codebase Rollback (Git)

1.  **Revert Merge Commit**:
    If the code has been merged to `main`, revert the merge commit.
    ```bash
    git revert -m 1 <merge_commit_hash>
    git push origin main
    ```

2.  **Restore Entrypoint**:
    Ensure `Dockerfile` is reverted to use `CMD ["gunicorn", ...]` and `app/main.py` restores Flask initialization logic if necessary (though the previous codebase should handle this).

## Database Considerations

-   **Migrations**: This migration **did not** introduce schema changes. Database rollback is not required for this code change.
-   **Data Integrity**: Ensure no partial data was written by the new services if they failed mid-transaction.

## Post-Rollback Verification

1.  **Health Check**: Verify `/system/health` returns 200 OK.
2.  **Critical Paths**: Test login, chat, and admin interfaces manually.
