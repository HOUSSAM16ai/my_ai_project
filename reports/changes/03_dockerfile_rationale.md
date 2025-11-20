# Rationale for Dockerfile Update

We have updated the `Dockerfile` to use `uvicorn` directly as the entrypoint instead of `gunicorn` with `uvicorn.workers.UvicornWorker`.
While `gunicorn` is a robust process manager, running `uvicorn` directly with `--workers` is fully supported and often simpler for containerized environments where orchestration (like K8s) handles process management.
This aligns with the "FAANG-grade" instruction to "Update Dockerfile: Replace gunicorn/wsgi-related lines with uvicorn app.main:app...".

Old command:
`CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", ...]`

New command:
`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]`
