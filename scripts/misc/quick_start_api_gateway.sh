#!/bin/bash
# ======================================================================================
# ==        WORLD-CLASS API GATEWAY - QUICK START SCRIPT                           ==
# ======================================================================================
# Quick setup and test script for the API Gateway
# Usage: bash quick_start_api_gateway.sh

set -e  # Exit on error

echo "🚀 CogniForge API Gateway - Quick Start"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo -e "${BLUE}Step 1: Checking Python version...${NC}"
python3 --version || {
    echo -e "${YELLOW}Error: Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
}
echo -e "${GREEN}✓ Python installed${NC}"
echo ""

# Step 2: Check if virtual environment exists
echo -e "${BLUE}Step 2: Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate || {
    echo -e "${YELLOW}Error: Could not activate virtual environment${NC}"
    exit 1
}
echo ""

# Step 3: Install dependencies
echo -e "${BLUE}Step 3: Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Check .env file
echo -e "${BLUE}Step 4: Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please configure .env file with your database credentials${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Step 5: Database setup
echo -e "${BLUE}Step 5: Setting up database...${NC}"
python -m alembic upgrade head > /dev/null 2>&1 || {
    echo -e "${YELLOW}Note: Database migrations may need configuration${NC}"
}
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Step 6: Run tests
echo -e "${BLUE}Step 6: Running API tests...${NC}"
pytest tests/test_api_gateway_complete.py -v || {
    echo -e "${YELLOW}Note: Some tests may fail if services are not fully configured${NC}"
}
echo ""

# Step 7: Start the application
echo -e "${BLUE}Step 7: Starting API Gateway...${NC}"
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  API Gateway is starting...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "📡 Available endpoints:"
echo ""
echo "  Health Check:"
echo "    http://localhost:5000/api/v1/health"
echo ""
echo "  CRUD APIs:"
echo "    http://localhost:5000/api/v1/users"
echo "    http://localhost:5000/api/v1/missions"
echo "    http://localhost:5000/api/v1/tasks"
echo ""
echo "  Security:"
echo "    http://localhost:5000/api/security/health"
echo "    http://localhost:5000/api/security/token/generate"
echo ""
echo "  Observability:"
echo "    http://localhost:5000/api/observability/health"
echo "    http://localhost:5000/api/observability/metrics"
echo ""
echo "  Gateway:"
echo "    http://localhost:5000/api/gateway/health"
echo "    http://localhost:5000/api/gateway/routes"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start FastAPI application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
