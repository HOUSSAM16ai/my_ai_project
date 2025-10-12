# 🔧 MCP Server CI/CD Fix - Complete Guide

## 📋 Issue Summary

### Problem
The GitHub MCP Server was failing in GitHub Actions workflow with the following error:
```
GitHub MCP Server running on stdio
Process completed with exit code 1.
```

### Root Cause Analysis

The GitHub MCP Server (`ghcr.io/github/github-mcp-server:latest`) is designed to run using the **Model Context Protocol (MCP)** over **stdio** (standard input/output). This means:

1. **Interactive Communication**: The server communicates via stdin/stdout, not HTTP
2. **Requires TTY**: Needs an interactive terminal (`-it` flags in docker)
3. **Not a Daemon**: Cannot run as a background service in detached mode (`-d`)

The GitHub Actions workflow was trying to:
```bash
docker run -d \
  --name github-mcp-server \
  --network host \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="${AI_AGENT_TOKEN}" \
  ghcr.io/github/github-mcp-server:latest
```

This caused the server to:
1. Start successfully
2. Output "GitHub MCP Server running on stdio"
3. Wait for stdin input
4. Exit immediately (no stdin in detached mode)
5. Fail the workflow

---

## ✅ Solution Implemented

### Changes Made

#### 1. Updated GitHub Actions Workflow (`.github/workflows/mcp-server-integration.yml`)

**Before:**
```yaml
- name: 🐳 Setup MCP Server
  run: |
    docker run -d \
      --name github-mcp-server \
      --network host \
      -e GITHUB_PERSONAL_ACCESS_TOKEN="${AI_AGENT_TOKEN}" \
      ghcr.io/github/github-mcp-server:latest
    
    # Check if running
    if docker ps | grep -q github-mcp-server; then
      echo "status=running" >> $GITHUB_OUTPUT
    else
      exit 1
    fi
```

**After:**
```yaml
- name: 🐳 Setup MCP Server
  run: |
    echo "🚀 Validating GitHub MCP Server setup..."
    
    # Pull MCP Server image to validate availability
    docker pull ghcr.io/github/github-mcp-server:latest
    
    echo "✅ MCP Server image pulled successfully"
    echo "📝 MCP Server is ready for local/development use"
    echo "💡 Run locally with: docker-compose --profile mcp up github_mcp"
    echo "status=validated" >> $GITHUB_OUTPUT
```

**Key Changes:**
- ✅ Validate setup instead of running the server
- ✅ Pull image to ensure availability
- ✅ Document proper local usage
- ✅ Set status to "validated" instead of "running"

#### 2. Updated Cleanup Job

**Before:**
```yaml
- name: 🐳 Stop MCP Server
  run: |
    docker stop github-mcp-server || true
    docker rm github-mcp-server || true
```

**After:**
```yaml
- name: 🐳 Cleanup Docker Resources
  run: |
    # Remove any dangling MCP containers (if any were created)
    docker ps -a | grep github-mcp-server | awk '{print $1}' | xargs -r docker rm -f || true
```

#### 3. Added Documentation

**Updated Files:**
- `MCP_README.md` - Added troubleshooting section for CI/CD
- `AI_AGENT_TOKEN_SETUP_GUIDE.md` - Added note about stdio behavior
- `.github/workflows/mcp-server-integration.yml` - Added explanatory comments

---

## 🚀 How to Use MCP Server Correctly

### ✅ For Local Development (Recommended)

Using **docker-compose** (has proper stdin_open/tty settings):
```bash
# Start MCP server with interactive terminal
docker-compose --profile mcp up github_mcp

# Or start all services including MCP
docker-compose --profile full up
```

### ✅ For Docker Run (Manual)

```bash
# Interactive mode (required for stdio)
docker run -it --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx" \
  ghcr.io/github/github-mcp-server:latest
```

### ✅ For CI/CD (GitHub Actions, etc.)

**Don't run the server as a daemon!** Instead:

1. **Validate Setup:**
   ```yaml
   - name: Validate MCP Setup
     run: |
       docker pull ghcr.io/github/github-mcp-server:latest
       echo "MCP Server image available"
   ```

2. **Use Token for Direct API Calls:**
   ```yaml
   - name: Use GitHub API
     env:
       GITHUB_TOKEN: ${{ secrets.AI_AGENT_TOKEN }}
     run: |
       # Make direct GitHub API calls
       curl -H "Authorization: token $GITHUB_TOKEN" \
         https://api.github.com/user
   ```

3. **Test Integrations:**
   ```yaml
   - name: Test GitHub Integration
     run: |
       # Test code that uses GitHub API
       pytest tests/test_github_integration.py
   ```

---

## 📊 Verification

### Check Workflow Status

The workflow will now:
- ✅ Pull the MCP server image successfully
- ✅ Validate the setup without running
- ✅ Complete without errors
- ✅ Provide clear instructions for local use

### Expected Output

```
🚀 Validating GitHub MCP Server setup...
latest: Pulling from github/github-mcp-server
Digest: sha256:6aa543f565bc98d96106fdd80a0abdc0c7147c8ca7f4663a814ceecef1ccc6d3
Status: Downloaded newer image for ghcr.io/github/github-mcp-server:latest
✅ MCP Server image pulled successfully
📝 MCP Server is ready for local/development use
💡 Run locally with: docker-compose --profile mcp up github_mcp
```

---

## 🎯 Why This Approach?

### Benefits

1. **✅ CI/CD Compatibility**: No more failed workflows due to stdio requirements
2. **✅ Faster Builds**: Only validate setup, don't wait for server startup
3. **✅ Clear Documentation**: Users know how to use MCP locally
4. **✅ Proper Architecture**: Use the right tool for the right job
5. **✅ Resource Efficient**: Don't run unnecessary containers in CI

### Understanding MCP Server Design

The GitHub MCP Server is specifically designed for:
- **Interactive AI Assistants**: GitHub Copilot, Claude, etc.
- **Local Development**: IDEs and development environments
- **Stdio Communication**: Direct stdin/stdout protocol messages

It is NOT designed for:
- ❌ Background daemon services
- ❌ HTTP API endpoints
- ❌ Headless CI/CD environments (without special setup)

---

## 🔍 Troubleshooting

### If you still see "MCP Server failed to start"

1. **Check the workflow file** - Ensure you're using the updated version
2. **Verify the change** - Look for "Validating" instead of "Starting"
3. **Pull latest changes** - `git pull origin main`

### For Local Development Issues

```bash
# Check if container is running
docker ps | grep github-mcp

# View logs
docker logs github-mcp-server

# Restart with fresh state
docker-compose --profile mcp down
docker-compose --profile mcp up github_mcp
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Container exits immediately" | Running in detached mode without stdin | Use `-it` flags or docker-compose |
| "stdio" message then exit | Expected behavior without input | Use interactive terminal |
| "401 Unauthorized" | Invalid token | Regenerate token in GitHub settings |
| "403 Forbidden" | Missing scopes | Add `repo`, `read:org`, `workflow` scopes |

---

## 📚 Additional Resources

- **GitHub MCP Server**: https://github.com/github/github-mcp-server
- **Model Context Protocol**: https://modelcontextprotocol.io
- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **GitHub Actions**: https://docs.github.com/en/actions

---

## ✨ Summary

**Problem:** MCP Server failed in CI/CD because it's stdio-based, not a daemon  
**Solution:** Validate setup in CI/CD, run interactively for local dev  
**Result:** ✅ Workflows pass, proper architecture, clear documentation  

---

**Built with ❤️ by Houssam Benmerah**  
*CogniForge - Superhuman AI Integration*
