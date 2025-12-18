#!/bin/bash
# =============================================================================
# CogniForge Superhuman UI - Quick Start Script
# =============================================================================
# This script sets up and runs the advanced UI/UX system
# Technologies: React, TypeScript, Three.js, D3.js, Plotly, Monaco Editor
# =============================================================================

set -e

echo "🚀 CogniForge Superhuman UI - Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo -e "${BLUE}📦 Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed!${NC}"
    echo "Please install Node.js (v18 or higher) from: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js $NODE_VERSION detected${NC}"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}⚠️  npm is not installed!${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ npm $NPM_VERSION detected${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    echo "Installing for the first time (this may take a few minutes)..."
    npm install
else
    echo "Dependencies already installed. Run 'npm install' to update."
fi
echo ""

# Build the frontend
echo -e "${BLUE}🔨 Building frontend...${NC}"
npm run build
echo -e "${GREEN}✅ Frontend built successfully!${NC}"
echo ""

# Check if Flask is running
echo -e "${BLUE}🌐 Starting Flask server...${NC}"
echo "The Superhuman UI will be available at:"
echo ""
echo -e "${GREEN}  👉 http://localhost:5000/superhuman-ui${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask
if command -v flask &> /dev/null; then
    flask run
else
    echo -e "${YELLOW}⚠️  Flask is not installed!${NC}"
    echo "Install Flask with: pip install -r requirements.txt"
    echo "Then run: flask run"
fi
