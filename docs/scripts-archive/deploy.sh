#!/bin/bash

echo "🚀 HCS Apple Technology Chatbot Deployment Script"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://api.tektest.org"
FRONTEND_URL="https://llm.tektest.org"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "   Backend URL:  $BACKEND_URL"
echo "   Frontend URL: $FRONTEND_URL"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites checked${NC}"
echo ""

# Setup backend
echo -e "${BLUE}🔧 Setting up backend...${NC}"

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo -e "${GREEN}✅ Backend setup complete${NC}"
echo ""

# Setup frontend
echo -e "${BLUE}🔧 Setting up frontend...${NC}"

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install > /dev/null 2>&1

# Build frontend for production
echo "Building frontend for production..."
REACT_APP_API_URL=$BACKEND_URL npm run build

echo -e "${GREEN}✅ Frontend build complete${NC}"
echo ""

# Instructions for running
echo -e "${YELLOW}📝 Deployment Instructions:${NC}"
echo ""
echo "1. Backend deployment (using Cloudflare Tunnel):"
echo "   - The backend is already configured to run on port 8000"
echo "   - Start the backend: python backend/app.py"
echo "   - Configure Cloudflare Tunnel to point to localhost:8000"
echo "   - Tunnel URL: $BACKEND_URL"
echo ""
echo "2. Frontend deployment (using Cloudflare Tunnel):"
echo "   - Serve the build folder on port 3000"
echo "   - Configure Cloudflare Tunnel to point to localhost:3000"
echo "   - Tunnel URL: $FRONTEND_URL"
echo ""
echo "3. To serve the production build locally:"
echo "   npm install -g serve (if not installed)"
echo "   serve -s build -l 3000"
echo ""
echo -e "${GREEN}✨ Deployment preparation complete!${NC}"