#!/bin/bash

echo "🚀 Starting HCS Apple Technology Chatbot (Production Mode)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your ANTHROPIC_API_KEY"
    exit 1
fi

# Check API key
LLM_PROVIDER=$(grep "LLM_PROVIDER=" .env | cut -d '=' -f2)
if [ "$LLM_PROVIDER" = "claude" ]; then
    if ! grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
        echo "⚠️  Please set your ANTHROPIC_API_KEY in the .env file"
        exit 1
    fi
    echo "✅ Using Claude API"
fi

# Build production frontend if needed
if [ ! -d "build" ]; then
    echo "📦 Building production frontend..."
    npm run build:prod
else
    echo "📁 Using existing production build"
fi

# Install serve if needed
if ! command -v npx &> /dev/null; then
    echo "📦 Installing Node.js dependencies..."
    npm install -g serve
fi

echo "🎯 Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

echo "🌐 Starting production frontend server..."
npx serve -s build -l 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ HCS Apple Technology Chatbot is running in PRODUCTION MODE!"
echo ""
echo "📱 Frontend: http://localhost:3000 (Production Build)"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Health: http://localhost:8000/health"
echo ""
echo "🌍 Tunnel this to: https://llm.tektest.org"
echo ""
echo "🚪 To stop the servers, press Ctrl+C"
echo ""

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

# Set trap to handle Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for either process to finish
wait