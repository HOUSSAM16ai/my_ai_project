# 🚀 GitHub MCP Server Integration - Quick Reference

## 🎯 What is this?

**GitHub Model Context Protocol (MCP) Server** integration for CogniForge - enabling AI assistants to interact directly with GitHub repositories, issues, pull requests, and more through a standardized, secure protocol.

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Get GitHub Token
Visit: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Select scopes: `repo`, `read:org`, `workflow`
- Copy the token (starts with `ghp_`)

### 2️⃣ Add to `.env`
```bash
GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3️⃣ Start MCP Server
```bash
# Quick setup script (recommended)
./quick_start_mcp.sh

# OR manually with Docker Compose
docker-compose --profile mcp up -d github_mcp

# OR manually with Docker
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}" \
  ghcr.io/github/github-mcp-server
```

---

## 🎯 Features

### ✨ GitHub Capabilities
- 📦 **Repository Management**: Create, read, update repositories
- 🐛 **Issue Tracking**: Create, comment, close issues
- 🔀 **Pull Requests**: Create, review, merge PRs
- 🔍 **Code Search**: Advanced search across all repositories
- ⚡ **GitHub Actions**: Manage and trigger workflows
- 👥 **Organizations**: Manage teams and permissions

### 🛡️ Security
- 🔐 Token encryption
- 📝 Audit logging
- 🚫 Protection from dangerous operations
- ⚠️ 90-day token rotation reminders

### 🌐 Platform Support
- ✅ VSCode
- ✅ Cursor IDE
- ✅ GitHub Codespaces
- ✅ Gitpod
- ✅ Dev Containers
- ✅ Local Development

---

## 📁 Configuration Files

```
.vscode/mcp-settings.json    # VSCode MCP configuration
.cursor/mcp.json             # Cursor IDE MCP configuration
docker-compose.yml           # MCP service definition
.env                         # GitHub token (DO NOT COMMIT!)
```

---

## 🔐 Security Best Practices

### ✅ DO:
- Store tokens in `.env` (already in `.gitignore`)
- Use GitHub Codespaces Secrets for cloud environments
- Rotate tokens every 90 days
- Use minimal required scopes
- Enable token expiration

### ⛔ DON'T:
- Never commit tokens to Git
- Never share tokens via email/screenshots
- Don't use same token for multiple projects
- Don't give more permissions than needed

---

## 🧪 Verification

```bash
# Check if container is running
docker ps | grep github-mcp

# View logs
docker logs github-mcp-server

# Check environment variable
docker exec github-mcp-server env | grep GITHUB
```

---

## 🛠️ Troubleshooting

### Container not running?
```bash
docker-compose logs github_mcp
docker-compose restart github_mcp
```

### Container exits immediately in CI/CD?
**This is expected!** The GitHub MCP Server runs on stdio (standard input/output) for MCP protocol communication. It's designed for interactive use with AI assistants in local development, not as a background daemon.

**In CI/CD (GitHub Actions, etc.):**
- ✅ Validate setup by pulling the image
- ✅ Use the token for direct GitHub API calls
- ❌ Don't try to run the server in detached mode

**For local development:**
```bash
# Use docker-compose with interactive terminal support
docker-compose --profile mcp up github_mcp

# Or with docker run (requires interactive terminal)
docker run -it --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" \
  ghcr.io/github/github-mcp-server:latest
```

### 401 Unauthorized?
- Token is invalid or expired
- Generate new token and update `.env`

### 403 Forbidden?
- Token lacks required permissions
- Add scopes: `repo`, `read:org`, `workflow`

---

## 📚 Documentation

- 📖 **Full Guide**: [MCP_INTEGRATION_GUIDE_AR.md](./MCP_INTEGRATION_GUIDE_AR.md)
- 📖 **GitHub MCP Server**: https://github.com/github/github-mcp-server
- 📖 **Model Context Protocol**: https://modelcontextprotocol.io
- 📖 **GitHub API**: https://docs.github.com/en/rest

---

## 🎯 Usage with IDEs

### VSCode
1. Open project in VSCode
2. Configuration auto-detected from `.vscode/mcp-settings.json`
3. GitHub Copilot will use MCP for GitHub operations

### Cursor IDE
1. Open project in Cursor
2. Configuration loaded from `.cursor/mcp.json`
3. Enter token when prompted (or use from `.env`)

---

## 🚀 Advanced Usage

### Start with specific profile:
```bash
# Start all services including MCP
docker-compose --profile full up -d

# Start only MCP service
docker-compose --profile mcp up -d github_mcp
```

### Manual Docker run:
```bash
docker run -d \
  --name github-mcp-server \
  --network host \
  --restart unless-stopped \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}" \
  ghcr.io/github/github-mcp-server
```

### Monitor logs:
```bash
# Follow logs
docker logs -f github-mcp-server

# Last 100 lines
docker logs --tail 100 github-mcp-server

# Save to file
docker logs github-mcp-server > mcp-logs.txt
```

---

## 📊 Container Information

**Image**: `ghcr.io/github/github-mcp-server:latest`  
**Container Name**: `github-mcp-server`  
**Network**: `host` (for local development)  
**Restart Policy**: `unless-stopped`  
**Resource Limits**: 512MB RAM, 1 CPU

---

## 🎉 What You Can Do Now

With GitHub MCP Server, AI assistants can:

✅ **Read** repository contents, issues, PRs  
✅ **Create** issues, PRs, comments  
✅ **Update** issue status, PR reviews  
✅ **Search** code across all repositories  
✅ **Trigger** GitHub Actions workflows  
✅ **Manage** teams and permissions  

---

## 💡 Example Scenarios

### Scenario 1: Issue Management
"Create an issue in repo X about bug Y, assign to user Z, and add labels 'bug' and 'priority-high'"

### Scenario 2: Code Search
"Find all occurrences of function `DatabaseService.connect()` in Python files across all my repositories"

### Scenario 3: PR Automation
"Create a PR from branch 'feature/new-api' to 'main' with title 'Add new API endpoints' and request review from @teammate"

### Scenario 4: Workflow Triggering
"Trigger the deployment workflow for the production environment"

---

## 🔄 Maintenance

### Update MCP Server:
```bash
docker pull ghcr.io/github/github-mcp-server:latest
docker-compose --profile mcp up -d --force-recreate github_mcp
```

### Clean old images:
```bash
docker image prune -a
```

### Rotate token (every 90 days):
1. Generate new token at https://github.com/settings/tokens
2. Update `.env` file
3. Restart container: `docker-compose restart github_mcp`

---

## 📞 Support

Having issues? Check:
1. **Troubleshooting section** above
2. **Full documentation**: MCP_INTEGRATION_GUIDE_AR.md
3. **GitHub logs**: `docker logs github-mcp-server`
4. **GitHub MCP Server Issues**: https://github.com/github/github-mcp-server/issues

---

## 🌟 Key Files

| File | Purpose |
|------|---------|
| `.vscode/mcp-settings.json` | VSCode MCP configuration |
| `.cursor/mcp.json` | Cursor IDE MCP configuration |
| `docker-compose.yml` | MCP service definition |
| `.env` | GitHub token storage (git-ignored) |
| `quick_start_mcp.sh` | Interactive setup script |
| `MCP_INTEGRATION_GUIDE_AR.md` | Complete documentation |

---

## ✅ Checklist

Before using MCP, ensure:
- [ ] Docker is installed and running
- [ ] `.env` file exists with valid `GITHUB_PERSONAL_ACCESS_TOKEN`
- [ ] Token has required scopes: `repo`, `read:org`, `workflow`
- [ ] MCP container is running: `docker ps | grep github-mcp`
- [ ] IDE configuration files exist (`.vscode/` or `.cursor/`)

---

**🚀 Built with ❤️ by CogniForge Team**

*Superhuman technology surpassing Google, Microsoft, OpenAI, and Apple! 🔥*

---

*Version: 1.0.0 | Last Updated: 2025-10-12 | Status: Production Ready ✅*
