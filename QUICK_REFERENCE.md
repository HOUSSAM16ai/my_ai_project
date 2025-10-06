# 🚀 CogniForge - Quick Reference Card
# بطاقة مرجعية سريعة

> **One-page reference for all platforms**

---

## 🌍 Platform Support

| Platform | Status | Access |
|----------|--------|--------|
| **Gitpod** | ✅ | `https://gitpod.io/#https://github.com/HOUSSAM16ai/my_ai_project` |
| **GitHub Codespaces** | ✅ | Code → Codespaces → Create codespace |
| **Dev Containers** | ✅ | Ctrl+Shift+P → "Reopen in Container" |
| **Local** | ✅ | `git clone` + `./quick-start.sh` |

---

## ⚡ Quick Start (Any Platform)

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env: Set DATABASE_URL with your Supabase connection string

# 2. One-command setup (recommended)
./quick-start.sh

# 3. Manual setup
pip install -r requirements.txt
docker-compose up -d
docker-compose run --rm web flask db upgrade
docker-compose run --rm web flask users create-admin
```

---

## 🗄️ Database Configuration

**Required**: Supabase PostgreSQL (cloud-based for all platforms)

```bash
# In .env file:
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Get it from:
# 1. https://supabase.com → Your Project
# 2. Settings → Database → Connection String (pooler)
```

---

## 🔧 Essential Commands

### Docker Commands
```bash
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f            # View logs
docker-compose ps                 # Check status
docker-compose restart            # Restart all
```

### Database Commands
```bash
docker-compose run --rm web flask db upgrade     # Run migrations
docker-compose run --rm web flask db current     # Show current version
docker-compose run --rm web flask db health      # Check health
docker-compose run --rm web flask db stats       # Show statistics
docker-compose run --rm web flask db tables      # List tables
```

### User Management
```bash
docker-compose run --rm web flask users create-admin    # Create admin
docker-compose run --rm web flask users list            # List users
```

### Helper Scripts
```bash
./detect_platform.sh              # Detect current platform
./quick-start.sh                  # Automated setup
./quick-start.sh --auto           # Non-interactive setup
```

---

## 🌐 Access URLs

| Service | Local | Gitpod | Codespaces |
|---------|-------|--------|------------|
| **Main App** | `http://localhost:5000` | Auto-forwarded | Ports tab → 5000 |
| **Admin Dashboard** | `http://localhost:5000/admin/dashboard` | Same + `/admin/dashboard` | Same + `/admin/dashboard` |
| **Database Admin** | `http://localhost:5000/admin/database` | Same + `/admin/database` | Same + `/admin/database` |
| **AI Service** | `http://localhost:8001` | Auto-forwarded | Ports tab → 8001 |

---

## 👤 Default Credentials

```
Email:    benmerahhoussam16@gmail.com
Password: 1111
```

**⚠️ Change these in production!**

---

## 📁 Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 5000 | Flask Web | Main application |
| 8000 | Dev Server | Alternative dev port |
| 8001 | FastAPI AI | AI microservice |

---

## 🔍 Troubleshooting Quick Fixes

### "Cannot connect to database"
```bash
# Check DATABASE_URL
cat .env | grep DATABASE_URL

# Test connection
docker-compose run --rm web python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('DATABASE_URL'))"
```

### "Docker not running"
```bash
# Check Docker status
docker ps

# Start Docker Desktop (if using GUI)
# Or: sudo systemctl start docker (Linux)
```

### "Migrations fail"
```bash
# Ensure Supabase is accessible
# Check DATABASE_URL format
# Try manual migration
docker-compose run --rm web flask db upgrade
```

### "Port already in use"
```bash
# Stop existing services
docker-compose down

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use 5001 instead of 5000
```

---

## 📚 Documentation Links

- 🌍 **Multi-Platform Setup**: [`MULTI_PLATFORM_SETUP.md`](MULTI_PLATFORM_SETUP.md)
- 📖 **Full Setup Guide**: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
- 🗄️ **Database Guide**: [`DATABASE_SYSTEM_SUPREME_AR.md`](DATABASE_SYSTEM_SUPREME_AR.md)
- 🔧 **Platform Fix Report**: [`PLATFORM_FIX_REPORT_AR.md`](PLATFORM_FIX_REPORT_AR.md)
- 📝 **README**: [`README.md`](README.md)

---

## 🎯 Common Tasks

### Reset Database
```bash
# WARNING: This will delete all data!
docker-compose run --rm web flask db downgrade base
docker-compose run --rm web flask db upgrade
docker-compose run --rm web flask users create-admin
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f ai_service
```

### Rebuild Everything
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Update Dependencies
```bash
pip install -r requirements.txt
docker-compose build
docker-compose up -d
```

---

## 🚀 Development Workflow

### 1. Start Development
```bash
git pull origin main
docker-compose up -d
docker-compose logs -f
```

### 2. Make Changes
- Edit code in your IDE
- Changes auto-reload (Flask debug mode)

### 3. Test Changes
```bash
# Check logs
docker-compose logs -f web

# Run tests (if available)
docker-compose run --rm web pytest
```

### 4. Database Changes
```bash
# Create migration
docker-compose run --rm web flask db migrate -m "Description"

# Apply migration
docker-compose run --rm web flask db upgrade
```

### 5. Commit & Push
```bash
git add .
git commit -m "Description"
git push origin your-branch
```

---

## 💡 Pro Tips

- ✅ Always use Supabase for consistency across platforms
- ✅ Run `./detect_platform.sh` to check your environment
- ✅ Use `./quick-start.sh` for clean setups
- ✅ Keep `.env` secure (never commit it)
- ✅ Check logs regularly: `docker-compose logs -f`
- ✅ Test on multiple platforms before deploying

---

## 🆘 Get Help

| Issue Type | Where to Look |
|------------|---------------|
| Platform setup | `MULTI_PLATFORM_SETUP.md` |
| Database issues | `DATABASE_SYSTEM_SUPREME_AR.md` |
| General setup | `SETUP_GUIDE.md` |
| Environment config | `.env.example` |
| Platform detection | `./detect_platform.sh` |

---

## 📊 Project Structure

```
my_ai_project/
├── app/                          # Flask application
│   ├── models/                   # Database models
│   ├── routes/                   # API routes
│   └── services/                 # Business logic
├── ai_service/                   # FastAPI AI microservice
├── migrations/                   # Database migrations
├── .devcontainer/                # VS Code Dev Container config
│   ├── devcontainer.json
│   ├── on-create.sh
│   ├── on-start.sh
│   └── on-attach.sh
├── .gitpod.yml                   # Gitpod configuration
├── docker-compose.yml            # Docker orchestration
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── detect_platform.sh            # Platform detection script
├── quick-start.sh                # Quick setup script
└── MULTI_PLATFORM_SETUP.md       # Full platform guide
```

---

**🌟 CogniForge - Works Everywhere! 🌟**

*For detailed information, see the full documentation files*
