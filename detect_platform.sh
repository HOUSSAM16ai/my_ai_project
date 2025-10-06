#!/usr/bin/env bash
###############################################################################
# detect_platform.sh
#
# يكتشف المنصة الحالية (Gitpod, Codespaces, Dev Container, Local)
# ويعرض معلومات مفيدة للمطور
#
# Detects current development platform and shows helpful information
###############################################################################

set -Eeuo pipefail

# Colors
if [ -t 1 ]; then
  RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
  CYAN=$(printf '\033[36m'); MAGENTA=$(printf '\033[35m'); BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; MAGENTA=""; BOLD=""; RESET=""
fi

header() { printf "\n%s%s%s\n" "$BOLD$MAGENTA" "$1" "$RESET"; }
info()   { printf "%s[INFO]%s %s\n" "$CYAN" "$RESET" "$1"; }
success() { printf "%s[✓]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()   { printf "%s[⚠]%s %s\n" "$YELLOW" "$RESET" "$1"; }
error()  { printf "%s[✗]%s %s\n" "$RED" "$RESET" "$1" >&2; }

# Detect platform
PLATFORM="Unknown"
PLATFORM_DETAILS=""

if [ -n "${GITPOD_WORKSPACE_ID:-}" ]; then
  PLATFORM="Gitpod"
  PLATFORM_DETAILS="Workspace: ${GITPOD_WORKSPACE_ID}"
elif [ -n "${CODESPACES:-}" ] || [ -n "${GITHUB_CODESPACE_TOKEN:-}" ]; then
  PLATFORM="GitHub Codespaces"
  PLATFORM_DETAILS="Codespace: ${CODESPACE_NAME:-$(hostname)}"
elif [ -n "${REMOTE_CONTAINERS:-}" ] || [ -f "/.dockerenv" ]; then
  PLATFORM="Dev Container"
  PLATFORM_DETAILS="Container-based development"
else
  PLATFORM="Local"
  PLATFORM_DETAILS="Native development environment"
fi

# Display platform information
header "🌍 CogniForge Platform Detection"
echo ""
success "Platform: ${BOLD}${PLATFORM}${RESET}"
info "$PLATFORM_DETAILS"
echo ""

# Platform-specific tips
header "💡 Platform-Specific Tips"
echo ""

case "$PLATFORM" in
  "Gitpod")
    info "✅ Gitpod detected - ports are automatically exposed"
    info "🌐 Access your app via the 'Open Browser' button for port 5000"
    info "📝 Your workspace is persistent for this repository"
    info "⏰ Remember: 50 hours free per month"
    ;;
  
  "GitHub Codespaces")
    info "✅ Codespaces detected - GitHub integration active"
    info "🌐 Access via Ports tab → Forward port 5000"
    info "📝 Your changes are automatically synced to GitHub"
    info "⏰ Remember: 60 hours free per month"
    ;;
  
  "Dev Container")
    info "✅ Dev Container detected - full Docker environment"
    info "🌐 Access via http://localhost:5000"
    info "📝 Running in isolated container with all dependencies"
    info "💻 Best for local development with full control"
    ;;
  
  "Local")
    info "✅ Local environment detected"
    info "🌐 Access via http://localhost:5000"
    info "📝 Make sure Docker is running for containers"
    info "💻 Full control over your development environment"
    ;;
esac

echo ""

# Check environment configuration
header "🔍 Environment Check"
echo ""

# Check for .env file
if [ -f ".env" ]; then
  success ".env file exists"
  
  # Check if DATABASE_URL is configured
  if grep -q "^DATABASE_URL=" .env 2>/dev/null; then
    DB_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    
    if [[ "$DB_URL" == *"supabase.co"* ]]; then
      success "DATABASE_URL configured with Supabase ✓"
    elif [[ "$DB_URL" == *"@db:"* ]] || [[ "$DB_URL" == *"localhost"* ]]; then
      warn "DATABASE_URL points to local database"
      info "Consider using Supabase for multi-platform consistency"
    else
      info "DATABASE_URL configured with external database"
    fi
  else
    error "DATABASE_URL not found in .env"
    warn "Please configure DATABASE_URL with your Supabase connection string"
  fi
else
  error ".env file not found"
  info "Run: cp .env.example .env"
  info "Then configure your DATABASE_URL"
fi

echo ""

# Check Docker
header "🐳 Docker Status"
echo ""

if command -v docker >/dev/null 2>&1; then
  if docker ps >/dev/null 2>&1; then
    success "Docker is running and accessible"
    
    # Check if services are running
    if docker ps | grep -q "flask-frontend"; then
      success "Flask frontend container is running"
    else
      info "Flask frontend container not running"
      info "Start with: docker-compose up -d"
    fi
    
    if docker ps | grep -q "fastapi-ai-service"; then
      success "AI service container is running"
    else
      info "AI service container not running (optional)"
    fi
  else
    warn "Docker daemon not accessible"
    info "Make sure Docker is running"
  fi
else
  warn "Docker command not found"
  info "Install Docker to use containerized services"
fi

echo ""

# Quick start commands
header "🚀 Quick Start Commands"
echo ""

cat <<EOF
${BOLD}1. Setup Environment:${RESET}
   ${CYAN}cp .env.example .env${RESET}
   ${CYAN}# Edit .env and set DATABASE_URL${RESET}

${BOLD}2. Install Dependencies:${RESET}
   ${CYAN}pip install -r requirements.txt${RESET}

${BOLD}3. Run Migrations:${RESET}
   ${CYAN}docker-compose run --rm web flask db upgrade${RESET}

${BOLD}4. Create Admin User:${RESET}
   ${CYAN}docker-compose run --rm web flask users create-admin${RESET}

${BOLD}5. Start Services:${RESET}
   ${CYAN}docker-compose up -d${RESET}

${BOLD}6. View Logs:${RESET}
   ${CYAN}docker-compose logs -f${RESET}

${BOLD}7. Stop Services:${RESET}
   ${CYAN}docker-compose down${RESET}
EOF

echo ""

# Additional resources
header "📚 Resources"
echo ""
info "📖 Setup Guide: SETUP_GUIDE.md"
info "🌍 Multi-Platform Guide: MULTI_PLATFORM_SETUP.md"
info "🗄️ Database Guide: DATABASE_SYSTEM_SUPREME_AR.md"
info "📝 README: README.md"

echo ""
success "✨ Platform detection complete!"
echo ""
