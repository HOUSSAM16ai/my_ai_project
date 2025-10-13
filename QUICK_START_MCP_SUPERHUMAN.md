# 🚀 QUICK START: MCP Server with AI_AGENT_TOKEN

## ⚡ Super Fast Setup (2 Minutes!)

### Step 1: Get Your Token (30 seconds)

1. Visit: https://github.com/settings/tokens/new
2. Give it a name: "AI Agent Token"
3. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow`
   - ✅ `read:org`
4. Click "Generate token"
5. **Copy the token** (starts with `ghp_` or `github_pat_`)

### Step 2: Add to GitHub Secrets (60 seconds)

**One Secret, Three Locations:**

#### Location 1: GitHub Actions
```
Repository Settings → Secrets and variables → Actions → New repository secret
Name: AI_AGENT_TOKEN
Value: [paste your token]
```

#### Location 2: Codespaces
```
Your Settings → Codespaces → Secrets → New secret
Name: AI_AGENT_TOKEN
Value: [paste your token]
Repository access: Select this repo
```

#### Location 3: Dependabot
```
Repository Settings → Secrets and variables → Dependabot → New repository secret
Name: AI_AGENT_TOKEN
Value: [paste your token]
```

### Step 3: (Optional) Local Development

If you want to run locally:

```bash
# Copy example env
cp .env.example .env

# Edit .env and add your token
AI_AGENT_TOKEN="ghp_your_token_here"
```

## ✅ That's It!

### Verify It Works

```bash
# Run verification script
./verify_mcp_superhuman.sh
```

Expected output:
```
🔥 ✅ ALL TESTS PASSED! SUPERHUMAN STATUS ACHIEVED! ✅ 🔥
```

### What Happens Next?

#### In GitHub Actions (Automatic!)
- Token automatically loaded from secrets
- GitHub API access enabled
- AI-powered workflows activated
- Zero configuration needed!

#### In Codespaces (Automatic!)
- Token injected into environment
- Available as `$AI_AGENT_TOKEN`
- Works immediately on open
- Zero configuration needed!

#### In Docker Compose (Automatic!)
- Reads from .env file
- Dual token support
- MCP Server starts properly
- Zero configuration needed!

## 🎯 Usage Examples

### GitHub Actions Workflow
```yaml
- name: Use AI Agent Token
  env:
    AI_AGENT_TOKEN: ${{ secrets.AI_AGENT_TOKEN }}
  run: |
    # Token is automatically available!
    curl -H "Authorization: token ${AI_AGENT_TOKEN}" \
         https://api.github.com/user
```

### Codespaces Terminal
```bash
# Token is automatically available!
echo $AI_AGENT_TOKEN

# Use with GitHub CLI
gh api user
```

### Docker Compose
```bash
# Start MCP Server
docker-compose --profile mcp up -d github_mcp

# Check status
docker logs github-mcp-server

# Expected output:
# ✅ Using AI_AGENT_TOKEN for authentication
# ✅ Token format validated
# ✅ MCP Server environment ready
```

## 🔍 Troubleshooting

### "Token not found"
- Check you added it to the correct location
- Verify secret name is exactly `AI_AGENT_TOKEN`
- For Codespaces, check repository access

### "Authentication failed"
- Token may be expired - generate a new one
- Check token has required scopes
- Verify token wasn't revoked

### "Container exits immediately"
- Check `.env` file has token
- Verify wrapper script is executable
- Check docker logs for details

## 📚 More Information

- **Complete Guide:** `MCP_SUPERHUMAN_SOLUTION.md`
- **Architecture:** `AI_AGENT_TOKEN_ARCHITECTURE.md`
- **Verification:** `verify_mcp_superhuman.sh`

## 🎉 Success Criteria

✅ All three GitHub Secrets added  
✅ Verification script passes  
✅ GitHub Actions workflows work  
✅ Codespaces auto-loads token  
✅ Docker Compose starts MCP Server  

**You're now running SUPERHUMAN AI technology!**

---

**Built with ❤️ by CogniForge**  
*Surpassing Google, Microsoft, OpenAI, and Apple!*
