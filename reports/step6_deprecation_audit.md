# Step 6: Deprecation Audit Report

This report documents the deprecated GitHub Actions that were identified and upgraded as part of the CI resurrection process.

## Summary of Findings

| Workflow File | Deprecated Action | Old Version | New Version |
|---|---|---|---|
| `.github/workflows/required-ci.yml` | `actions/upload-artifact` | `v3` | `v4` |
| `.github/workflows/cli-layer-smoke.yml` | `actions/setup-python` | `v4` | `v5` |
| `.github/workflows/dependency-layer-smoke.yml` | `actions/checkout` | `v3` | `v4` |
| `.github/workflows/dependency-layer-smoke.yml` | `actions/setup-python` | `v4` | `v5` |
| `.github/workflows/migration-readiness.yml` | `actions/setup-python` | `v4` | `v5` |
| `.github/workflows/transcendent.yml` | `actions/checkout` | `v3` | `v4` |
| `.github/workflows/transcendent.yml` | `actions/setup-python` | `v4` | `v5` |
| `.github/workflows/ultimate-ci.yml` | `dorny/paths-filter` | `v3` | `v4` |
| `.github/workflows/ultimate-ci.yml` | `nick-invision/retry` | `v3` | `v4` |

All identified actions have been successfully upgraded to their latest stable versions to ensure compatibility and security.
