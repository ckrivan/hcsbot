#!/bin/bash

# HCS Chatbot - Local LLM Setup Script
# Downloads and configures Llama 3.2 7B model

set -e

echo "🤖 HCS Chatbot - Local LLM Setup"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Ollama container is running
if ! docker-compose ps ollama | grep -q "Up"; then
    echo -e "${RED}❌ Ollama container is not running. Please run './deploy-docker.sh' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ollama container is running${NC}"

# Check if model is already downloaded
echo -e "${BLUE}🔍 Checking for existing models...${NC}"
EXISTING_MODELS=$(docker-compose exec -T ollama ollama list 2>/dev/null | grep -v "NAME" | wc -l || echo "0")

if [ "$EXISTING_MODELS" -gt 0 ]; then
    echo -e "${GREEN}✅ Found existing models:${NC}"
    docker-compose exec -T ollama ollama list
    echo ""
    read -p "Do you want to download additional models? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Using existing models${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}📋 Available models for HCS Apple Technology Assistant:${NC}"
echo ""
echo "1. llama3.2:7b (Recommended) - 4.1GB - Best balance of quality and speed"
echo "2. llama3.2:3b - 2.0GB - Faster, good quality"
echo "3. llama3.2:1b - 1.3GB - Fastest, basic quality"
echo "4. codellama:7b - 3.8GB - Optimized for technical documentation"
echo "5. mistral:7b - 4.1GB - Good alternative to Llama"
echo ""

read -p "Select model (1-5, default: 1): " -n 1 -r MODEL_CHOICE
echo ""

case $MODEL_CHOICE in
    2)
        MODEL_NAME="llama3.2:3b"
        MODEL_SIZE="2.0GB"
        ;;
    3)
        MODEL_NAME="llama3.2:1b"
        MODEL_SIZE="1.3GB"
        ;;
    4)
        MODEL_NAME="codellama:7b"
        MODEL_SIZE="3.8GB"
        ;;
    5)
        MODEL_NAME="mistral:7b"
        MODEL_SIZE="4.1GB"
        ;;
    *)
        MODEL_NAME="llama3.2:7b"
        MODEL_SIZE="4.1GB"
        ;;
esac

echo -e "${BLUE}📥 Downloading ${MODEL_NAME} (${MODEL_SIZE})...${NC}"
echo -e "${YELLOW}⏳ This may take 5-15 minutes depending on your internet speed${NC}"

# Download the model
if docker-compose exec -T ollama ollama pull "$MODEL_NAME"; then
    echo -e "${GREEN}✅ Successfully downloaded ${MODEL_NAME}${NC}"
else
    echo -e "${RED}❌ Failed to download ${MODEL_NAME}${NC}"
    exit 1
fi

# Update the .env file with the selected model
echo -e "${BLUE}🔧 Updating configuration...${NC}"
if [ -f ".env" ]; then
    # Create backup
    cp .env .env.backup
    
    # Update the model in .env file
    if grep -q "OLLAMA_MODEL=" .env; then
        sed -i.bak "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL_NAME/" .env
    else
        echo "OLLAMA_MODEL=$MODEL_NAME" >> .env
    fi
    
    echo -e "${GREEN}✅ Updated .env with model: ${MODEL_NAME}${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Test the model
echo -e "${BLUE}🧪 Testing model...${NC}"
TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'$MODEL_NAME'",
        "prompt": "What is Apple Business Manager?",
        "stream": false,
        "options": {"num_predict": 50}
    }' | grep -o '"response":"[^"]*"' | cut -d'"' -f4 | head -c 100)

if [ ! -z "$TEST_RESPONSE" ]; then
    echo -e "${GREEN}✅ Model is working correctly${NC}"
    echo -e "${BLUE}Sample response: ${TEST_RESPONSE}...${NC}"
else
    echo -e "${YELLOW}⚠️  Model downloaded but test failed. This may be normal.${NC}"
fi

# Restart backend to pick up new model
echo -e "${BLUE}🔄 Restarting backend service...${NC}"
docker-compose restart hcs-backend

echo ""
echo -e "${GREEN}🎉 Local LLM setup complete!${NC}"
echo ""
echo "🤖 Model: $MODEL_NAME"
echo "📊 Size: $MODEL_SIZE"
echo "🔗 API: http://localhost:11434"
echo ""
echo -e "${YELLOW}💡 Pro tips:${NC}"
echo "• Test the model: curl http://localhost:11434/api/tags"
echo "• View backend logs: docker-compose logs -f hcs-backend"
echo "• Monitor GPU usage: docker stats"
echo ""
echo -e "${BLUE}🚀 Ready to use HCS Apple Technology Assistant with local LLM!${NC}"