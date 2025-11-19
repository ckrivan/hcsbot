#!/bin/bash

echo "🚀 Starting HCS Apple Technology Chatbot..."

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
    echo "📝 Please edit .env file and add your OPENAI_API_KEY"
    echo "   Then run this script again."
    exit 1
fi

# Check if required API key is set based on provider
LLM_PROVIDER=$(grep "LLM_PROVIDER=" .env | cut -d '=' -f2)
USE_OLLAMA=$(grep "USE_OLLAMA=" .env | cut -d '=' -f2)

if [ "$USE_OLLAMA" = "true" ]; then
    echo "✅ Using Ollama - no API key required"
elif [ "$LLM_PROVIDER" = "claude" ]; then
    if ! grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
        echo "⚠️  Please set your ANTHROPIC_API_KEY in the .env file"
        echo "   Then run this script again."
        exit 1
    fi
    echo "✅ Using Claude API"
else
    if ! grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "⚠️  Please set your OPENAI_API_KEY in the .env file"
        echo "   Then run this script again."
        exit 1
    fi
    echo "✅ Using OpenAI API"
fi

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🎯 Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

echo "🌐 Starting frontend server..."
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ HCS Apple Technology Chatbot is starting up!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Health: http://localhost:8000/health"
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