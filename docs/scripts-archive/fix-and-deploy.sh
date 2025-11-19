#!/bin/bash

# HCS Chatbot - Fix Docker Issues and Deploy
echo "🔧 Fixing Docker configuration and deploying..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Stop any running containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Clean up any cached builds
echo -e "${BLUE}🧹 Cleaning Docker cache...${NC}"
docker system prune -f

# Remove the version line that causes warnings
echo -e "${BLUE}📝 Updating docker-compose.yml...${NC}"
sed -i.bak '1s/version: .*/# Docker Compose for HCS Chatbot/' docker-compose.yml 2>/dev/null || true

# Rebuild with no cache to avoid issues
echo -e "${BLUE}🔨 Building containers...${NC}"
docker-compose build --no-cache

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 15

# Check health
echo -e "${BLUE}🔍 Checking service health...${NC}"

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not responding yet (check logs)${NC}"
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running!${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend not responding yet (check logs)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "📱 Frontend: http://192.168.86.100:3000"
echo "🔧 Backend: http://192.168.86.100:8000"
echo ""
echo "📋 Check logs: docker-compose logs -f"
echo "🔍 Check status: docker-compose ps"