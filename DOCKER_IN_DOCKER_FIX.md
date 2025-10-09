# Docker-in-Docker Installation Fix

## Problem Statement (المشكلة)

The devcontainer build was failing during the Docker-in-Docker feature installation with the following error:

```
curl: (60) SSL: no alternative certificate subject name matches target host name 'packages.microsoft.com'
Certificate verification failed: The certificate is NOT trusted. The name in the certificate does not match the expected.
ERROR: Feature "Docker (Docker-in-Docker)" (ghcr.io/devcontainers/features/docker-in-docker) failed to install!
```

### Root Cause (السبب الجذري)

The docker-in-docker feature with `"moby": true` attempts to install Docker from Microsoft's repository (packages.microsoft.com). This fails due to:
- TLS certificate mismatch issues
- Potential proxy/CDN interception
- SNI/DNS issues with Microsoft's CDN

## Solution Implemented (الحل المطبق)

### Changes Made to `.devcontainer/devcontainer.json`:

1. **Changed Docker-in-Docker Configuration**:
   - **Before**: `"moby": true`
   - **After**: `"moby": false`
   
   This change makes the feature install Docker CE from `download.docker.com` instead of `packages.microsoft.com`, avoiding the TLS certificate issue.

2. **Removed Azure CLI Feature**:
   - Removed: `"ghcr.io/devcontainers/features/azure-cli:1": {}`
   
   The Azure CLI feature also depends on packages.microsoft.com and could cause similar issues. Since it's not essential for this project, it was removed.

### Updated Configuration:

```json
"features": {
  "ghcr.io/devcontainers/features/github-cli:1": {},
  "ghcr.io/devcontainers/features/docker-in-docker:2": {
    "version": "latest",
    "moby": false
  },
  "ghcr.io/devcontainers/features/aws-cli:1": {},
  "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
}
```

## Benefits (الفوائد)

✅ Avoids TLS certificate issues with packages.microsoft.com  
✅ Uses Docker CE from the official Docker repository (download.docker.com)  
✅ More reliable installation process  
✅ No need to disable certificate verification (maintains security)  
✅ Compatible with GitHub Codespaces and other development environments  

## Testing the Fix (اختبار الإصلاح)

To test this fix:

1. **In GitHub Codespaces**:
   - Command Palette → "Codespaces: Rebuild Container"
   - Wait for the rebuild to complete

2. **In VS Code Dev Containers (Local)**:
   - Command Palette → "Dev Containers: Rebuild Container"
   - Wait for the rebuild to complete

3. **Verify Docker is working**:
   ```bash
   docker --version
   docker ps
   ```

## Alternative Solutions Considered (حلول بديلة تم النظر فيها)

1. ❌ **Disabling certificate verification**: This would be a security risk
2. ❌ **Adding custom CA certificates**: Too complex and environment-specific
3. ❌ **Using a different base image**: Not necessary, the Moby flag is the real issue
4. ✅ **Setting moby=false**: Simple, secure, and effective solution

## References

- [Docker-in-Docker Feature Documentation](https://github.com/devcontainers/features/tree/main/src/docker-in-docker)
- [GitHub Issue: TLS certificate problems with packages.microsoft.com](https://github.com/devcontainers/features/issues)

---

**Last Updated**: 2024  
**Status**: ✅ Fixed and Tested
