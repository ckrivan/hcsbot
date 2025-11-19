#!/bin/bash

# HCS Chatbot - Cloudflare Tunnel Setup Script
# For Mac Mini M4 Server

set -e

echo "🌐 HCS Chatbot - Cloudflare Tunnel Setup"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if services are running
if ! docker-compose ps | grep -q "Up.*3000.*Up.*8000"; then
    echo -e "${RED}❌ Docker services are not running. Please run './deploy-docker.sh' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker services are running${NC}"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️  cloudflared not found. Installing...${NC}"
    if command -v brew &> /dev/null; then
        brew install cloudflared
    else
        echo -e "${RED}❌ Homebrew not found. Please install cloudflared manually.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ cloudflared is available${NC}"

# Check if tunnel config exists
if [ ! -f "tunnel-config.yml" ]; then
    echo -e "${YELLOW}⚠️  Tunnel config not found. You need to create a tunnel first.${NC}"
    echo ""
    echo "Run these commands first:"
    echo "1. cloudflared tunnel login"
    echo "2. cloudflared tunnel create hcs-api"
    echo "3. cloudflared tunnel route dns hcs-api hcs-api.tektest.org"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Tunnel configuration found${NC}"

# Start tunnel services
echo -e "${BLUE}🚀 Starting Cloudflare tunnels...${NC}"

# Start backend tunnel
echo -e "${BLUE}🔧 Starting backend API tunnel...${NC}"
docker-compose up -d cloudflared

echo -e "${BLUE}⏳ Waiting for tunnel to establish...${NC}"
sleep 10

# Test tunnel connectivity
echo -e "${BLUE}🔍 Testing tunnel connectivity...${NC}"
if curl -s https://hcs-api.tektest.org/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend tunnel is working${NC}"
else
    echo -e "${YELLOW}⚠️  Backend tunnel not responding yet (may still be connecting)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Tunnel setup complete!${NC}"
echo ""
echo "🌍 Public URLs:"
echo "   Backend API: https://hcs-api.tektest.org"
echo "   Frontend: https://llm.tektest.org (configure separately)"
echo ""
echo "🔍 Local URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Test backend: curl https://hcs-api.tektest.org/health"
echo "2. Configure frontend tunnel to point to localhost:3000"
echo "3. Update DNS if needed"
echo ""
echo -e "${BLUE}📊 Management:${NC}"
echo "• View tunnel logs: docker-compose logs -f cloudflared"
echo "• Stop tunnel: docker-compose stop cloudflared"
echo "• Restart tunnel: docker-compose restart cloudflared"