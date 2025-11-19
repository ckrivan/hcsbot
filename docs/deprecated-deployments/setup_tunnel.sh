#!/bin/bash

echo "🌐 Setting up Cloudflare Tunnel for HCS Apple Chatbot Demo"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install cloudflared
        else
            echo "❌ Please install Homebrew first, then run: brew install cloudflared"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared.deb
        rm cloudflared.deb
    else
        echo "❌ Unsupported OS. Please install cloudflared manually from:"
        echo "   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
fi

echo "✅ cloudflared is installed"
echo ""

# Check if the application is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "⚠️  Frontend application not detected on localhost:3000"
    echo "   Please start the application first with: ./start.sh"
    echo "   Then run this script in another terminal"
    exit 1
fi

echo "🚀 Creating tunnel to localhost:3000..."
echo ""
echo "📋 Tunnel Information:"
echo "   Local URL: http://localhost:3000"
echo "   Tunnel will provide a public URL for demo purposes"
echo ""
echo "🔗 Starting Cloudflare Tunnel..."
echo "   The public URL will be displayed below:"
echo ""

# Start the tunnel
cloudflared tunnel --url http://localhost:3000