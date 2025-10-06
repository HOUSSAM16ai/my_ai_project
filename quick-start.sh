#!/usr/bin/env bash
###############################################################################
# quick-start.sh
#
# سكريبت بدء سريع متعدد المنصات
# Quick start script for all platforms (Gitpod, Codespaces, Dev Containers, Local)
#
# Usage:
#   ./quick-start.sh          # Interactive setup
#   ./quick-start.sh --auto   # Automatic setup with defaults
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

header()  { printf "\n%s%s═══════════════════════════════════════════════════%s\n" "$BOLD$MAGENTA" "$1" "$RESET"; }
step()    { printf "%s[STEP %s]%s %s\n" "$CYAN" "$1" "$RESET" "$2"; }
success() { printf "%s[✓]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()    { printf "%s[⚠]%s %s\n" "$YELLOW" "$RESET" "$1"; }
error()   { printf "%s[✗]%s %s\n" "$RED" "$RESET" "$1" >&2; }
info()    { printf "   %s\n" "$1"; }

trap 'error "خطأ في السطر $LINENO. توقف التنفيذ."' ERR

AUTO_MODE=false
if [ "${1:-}" = "--auto" ]; then
  AUTO_MODE=true
fi

# Clear screen and show banner
clear
header "🌟 CogniForge Quick Start"
echo ""
echo "${BOLD}${CYAN}مرحبًا بك في CogniForge!${RESET}"
echo "Welcome to the Superior AI-Powered Educational Platform"
echo ""

# Detect platform
if [ -n "${GITPOD_WORKSPACE_ID:-}" ]; then
  PLATFORM="Gitpod"
elif [ -n "${CODESPACES:-}" ] || [ -n "${GITHUB_CODESPACE_TOKEN:-}" ]; then
  PLATFORM="GitHub Codespaces"
elif [ -n "${REMOTE_CONTAINERS:-}" ] || [ -f "/.dockerenv" ]; then
  PLATFORM="Dev Container"
else
  PLATFORM="Local"
fi

success "Platform detected: ${BOLD}${PLATFORM}${RESET}"
echo ""

# Step 1: Environment Setup
step "1/6" "Setting up environment..."
echo ""

if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    success "Created .env from .env.example"
    warn "⚠️  IMPORTANT: You need to configure DATABASE_URL in .env"
    echo ""
    info "Edit .env and set:"
    info "DATABASE_URL=postgresql://postgres.YOUR_PROJECT:PASSWORD@aws-0-region.pooler.supabase.com:5432/postgres"
    echo ""
    
    if [ "$AUTO_MODE" = false ]; then
      read -p "Press Enter after configuring .env file... "
    else
      warn "Running in auto mode - you must configure .env manually later"
      sleep 2
    fi
  else
    error ".env.example not found!"
    exit 1
  fi
else
  success ".env file already exists"
  
  # Check if DATABASE_URL is configured
  if grep -q "^DATABASE_URL=" .env 2>/dev/null; then
    DB_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    if [[ "$DB_URL" == *"supabase.co"* ]]; then
      success "DATABASE_URL configured with Supabase"
    else
      warn "DATABASE_URL found but might need updating"
    fi
  else
    warn "DATABASE_URL not found in .env - you'll need to add it"
  fi
fi

echo ""

# Step 2: Install Python dependencies
step "2/6" "Installing Python dependencies..."
echo ""

if [ -f "requirements.txt" ]; then
  if pip install --no-cache-dir -r requirements.txt; then
    success "Dependencies installed successfully"
  else
    error "Failed to install dependencies"
    exit 1
  fi
else
  error "requirements.txt not found!"
  exit 1
fi

echo ""

# Step 3: Check Docker
step "3/6" "Checking Docker..."
echo ""

if ! command -v docker >/dev/null 2>&1; then
  error "Docker not found!"
  info "Please install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker ps >/dev/null 2>&1; then
  error "Docker daemon not running!"
  info "Please start Docker and try again"
  exit 1
fi

success "Docker is running"
echo ""

# Step 4: Build Docker images
step "4/6" "Building Docker images..."
echo ""

if docker-compose build; then
  success "Docker images built successfully"
else
  error "Failed to build Docker images"
  exit 1
fi

echo ""

# Step 5: Run database migrations
step "5/6" "Running database migrations..."
echo ""

info "This will create all necessary database tables in your Supabase database"
echo ""

if docker-compose run --rm web flask db upgrade; then
  success "Database migrations completed"
else
  error "Migration failed - check your DATABASE_URL in .env"
  warn "Make sure your Supabase database is accessible"
  exit 1
fi

echo ""

# Step 6: Create admin user
step "6/6" "Creating admin user..."
echo ""

if docker-compose run --rm web flask users create-admin; then
  success "Admin user created (or already exists)"
  echo ""
  info "Default admin credentials:"
  info "  Email: benmerahhoussam16@gmail.com"
  info "  Password: 1111"
else
  warn "Failed to create admin user (it might already exist)"
fi

echo ""

# Final setup complete
header "✨ Setup Complete!"
echo ""

success "🎉 CogniForge is ready to use!"
echo ""

# Start services
echo "${BOLD}Do you want to start the services now?${RESET}"
if [ "$AUTO_MODE" = true ]; then
  START_NOW="y"
else
  read -p "Start services? [Y/n]: " START_NOW
  START_NOW=${START_NOW:-y}
fi

if [[ "$START_NOW" =~ ^[Yy] ]]; then
  echo ""
  step "START" "Starting services..."
  echo ""
  
  if docker-compose up -d; then
    success "Services started successfully!"
    echo ""
    
    # Show access information based on platform
    info "${BOLD}Access your application:${RESET}"
    case "$PLATFORM" in
      "Gitpod")
        info "🌐 Click 'Open Browser' when prompted for port 5000"
        info "   Or check the 'Ports' tab in Gitpod"
        ;;
      "GitHub Codespaces")
        info "🌐 Go to 'Ports' tab and click the globe icon for port 5000"
        info "   Or use the forwarded URL shown in Ports tab"
        ;;
      "Dev Container"|"Local")
        info "🌐 http://localhost:5000"
        ;;
    esac
    
    echo ""
    info "${BOLD}Admin Dashboard:${RESET}"
    info "📊 /admin/dashboard"
    info "🗄️  /admin/database"
    echo ""
    info "${BOLD}Credentials:${RESET}"
    info "📧 Email: benmerahhoussam16@gmail.com"
    info "🔑 Password: 1111"
    echo ""
    
    # Show logs option
    echo "${BOLD}View logs?${RESET}"
    if [ "$AUTO_MODE" = false ]; then
      read -p "Show live logs? [y/N]: " SHOW_LOGS
      SHOW_LOGS=${SHOW_LOGS:-n}
      
      if [[ "$SHOW_LOGS" =~ ^[Yy] ]]; then
        echo ""
        info "Showing logs (Ctrl+C to stop)..."
        sleep 1
        docker-compose logs -f
      fi
    fi
  else
    error "Failed to start services"
    exit 1
  fi
else
  echo ""
  info "Services not started. Start them manually with:"
  info "  ${CYAN}docker-compose up -d${RESET}"
fi

echo ""
header "📚 Next Steps"
echo ""

cat <<EOF
${BOLD}Useful Commands:${RESET}

  ${CYAN}docker-compose logs -f${RESET}          # View logs
  ${CYAN}docker-compose ps${RESET}               # Check service status
  ${CYAN}docker-compose down${RESET}             # Stop services
  ${CYAN}docker-compose restart${RESET}          # Restart services
  ${CYAN}./detect_platform.sh${RESET}            # Platform information

${BOLD}Documentation:${RESET}

  📖 ${CYAN}MULTI_PLATFORM_SETUP.md${RESET}      # Multi-platform guide
  📖 ${CYAN}SETUP_GUIDE.md${RESET}               # Detailed setup guide
  📖 ${CYAN}DATABASE_SYSTEM_SUPREME_AR.md${RESET} # Database guide

${BOLD}Database Management:${RESET}

  ${CYAN}flask db health${RESET}                 # Check database health
  ${CYAN}flask db stats${RESET}                  # Show statistics
  ${CYAN}flask db tables${RESET}                 # List all tables

EOF

echo ""
success "✨ Happy coding with CogniForge!"
echo ""
