#!/bin/bash
# =============================================================================
# CogniForge Environment Setup Script
# =============================================================================
# This script helps you set up the .env file correctly for local development
#
# Usage:
#   ./setup-env.sh
#
# Author: Houssam Benmerah
# =============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}CogniForge Environment Setup${NC}"
echo -e "${BLUE}================================${NC}\n"

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists!${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Setup cancelled.${NC}"
        exit 1
    fi
fi

# Copy .env.example to .env
echo -e "${BLUE}📋 Creating .env from .env.example...${NC}"
cp .env.example .env

echo -e "${GREEN}✅ .env file created successfully!${NC}\n"

# Check and warn about database configuration
echo -e "${BLUE}🔍 Checking database configuration...${NC}"
if grep -q "your-project-id" .env; then
    echo -e "${YELLOW}⚠️  WARNING: DATABASE_URL still contains placeholder values!${NC}"
    echo -e "${YELLOW}   You need to choose a database configuration:${NC}\n"
    
    echo -e "${BLUE}Choose database mode:${NC}"
    echo "  1) Local Database (Docker Compose) - Recommended for development"
    echo "  2) Remote Supabase - For production or remote access"
    echo ""
    read -p "Enter your choice (1 or 2): " -n 1 -r DB_CHOICE
    echo
    
    if [[ $DB_CHOICE == "1" ]]; then
        echo -e "${BLUE}📝 Configuring for LOCAL database...${NC}"
        
        # Replace the database configuration section
        sed -i.bak '/^# OPTION 1:/,/^# DATABASE_URL=/c\
# OPTION 1: LOCAL DATABASE (Default - for Docker Compose)\
# Use this for local development with docker-compose\
DATABASE_PASSWORD=Aog2Df4lIlIXiCGk\
DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD}@db:5432/postgres' .env
        
        # Comment out Supabase options
        sed -i.bak 's/^SUPABASE_URL=/# SUPABASE_URL=/g' .env
        sed -i.bak 's/^SUPABASE_KEY=/# SUPABASE_KEY=/g' .env
        
        echo -e "${GREEN}✅ Configured for LOCAL database (db:5432)${NC}"
        
    elif [[ $DB_CHOICE == "2" ]]; then
        echo -e "${BLUE}📝 Configuring for REMOTE Supabase...${NC}"
        echo -e "${YELLOW}⚠️  You'll need to manually edit .env with your Supabase credentials${NC}"
        echo ""
        echo "Required values:"
        echo "  - SUPABASE_URL"
        echo "  - SUPABASE_KEY"
        echo "  - DATABASE_URL (Supabase connection string)"
        
    else
        echo -e "${YELLOW}⚠️  Invalid choice. Please edit .env manually.${NC}"
    fi
fi

# Check for API keys
echo ""
echo -e "${BLUE}🔑 Checking API keys...${NC}"
if grep -q "your-openrouter-api-key" .env; then
    echo -e "${YELLOW}⚠️  OpenRouter API key is still a placeholder${NC}"
    echo -e "${YELLOW}   Update OPENROUTER_API_KEY in .env with your actual key${NC}"
fi

# Final instructions
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}\n"
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review and update .env file if needed"
echo "  2. Start services: ${BLUE}docker-compose up -d${NC}"
echo "  3. Run migrations: ${BLUE}docker-compose run --rm web flask db upgrade${NC}"
echo "  4. Create admin user: ${BLUE}docker-compose run --rm web flask users create-admin${NC}"
echo ""
echo -e "${BLUE}📚 For more help, see SETUP_GUIDE.md${NC}"
echo ""
