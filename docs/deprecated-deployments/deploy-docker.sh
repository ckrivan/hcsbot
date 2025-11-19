#!/bin/bash

# HCS Chatbot Docker Deployment Script
# For Mac Mini M4 Server with Local LLM

set -e

echo "🚀 HCS Apple Technology Chatbot - Docker Deployment"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Use Docker environment configuration
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📋 Using Docker configuration (.env.docker)${NC}"
    cp .env.docker .env
    echo -e "${GREEN}✅ Environment configured for Mac Mini server${NC}"
fi

# Create PDFs directory if it doesn't exist
if [ ! -d "backend/pdfs" ]; then
    mkdir -p backend/pdfs
    echo -e "${GREEN}✅ Created pdfs directory${NC}"
    
    # Copy some demo PDFs
    if [ -d "PDFs" ]; then
        echo -e "${BLUE}📄 Copying PDF documents...${NC}"
        cp PDFs/*.pdf backend/pdfs/ 2>/dev/null || true
        echo -e "${GREEN}✅ Copied $(ls backend/pdfs/*.pdf 2>/dev/null | wc -l | tr -d ' ') PDF documents${NC}"
    fi
fi

# Build production frontend first
echo -e "${BLUE}📦 Building production frontend...${NC}"
if [ ! -d "build" ]; then
    echo "Building React app for production..."
    REACT_APP_API_URL=http://192.168.86.100:8000 npm run build
    echo -e "${GREEN}✅ Frontend built${NC}"
else
    echo -e "${YELLOW}🔄 Rebuilding with correct API URL...${NC}"
    REACT_APP_API_URL=http://192.168.86.100:8000 npm run build
    echo -e "${GREEN}✅ Frontend rebuilt${NC}"
fi

echo -e "${BLUE}🐳 Building Docker images...${NC}"
docker-compose build --no-cache

echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 15

# Check service health
echo -e "${BLUE}🔍 Checking service health...${NC}"

# Check Ollama
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama service is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama service not responding (this is normal on first startup)${NC}"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis service is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis service not responding${NC}"
fi

# Check backend
echo -e "${BLUE}⏳ Waiting for backend to initialize...${NC}"
sleep 10
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend service is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend service not responding yet (may still be initializing)${NC}"
fi

# Check frontend
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend service is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service not responding yet...${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "📱 Frontend: http://192.168.86.100:3000"
echo "🔧 Backend API: http://192.168.86.100:8000"
echo "📊 Redis: 192.168.86.100:6379"
echo ""
echo -e "${YELLOW}💰 Using GPT-4o Mini API (very cost effective!)${NC}"
echo "• ~95% cheaper than Claude 3.5 Sonnet"
echo "• ~$0.005 per query (vs $0.05-0.30 with Claude)"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Set up Cloudflare tunnel: ./setup-tunnel.sh"
echo "2. Monitor logs: docker-compose logs -f"
echo "3. Check health: curl http://192.168.86.100:8000/health"
echo "4. Access from any device on your network!"
echo ""
echo -e "${BLUE}📊 Management commands:${NC}"
echo "🛑 Stop all: docker-compose down"
echo "🔄 Restart: docker-compose restart"
echo "📜 View logs: docker-compose logs -f [service-name]"
echo "🔍 Service status: docker-compose ps"