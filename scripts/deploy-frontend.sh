#!/bin/bash

# Frontend Deployment Script for HCSBot
# This script rebuilds and restarts the React frontend

echo "🚀 Starting frontend deployment..."

# Navigate to project directory
cd /var/www/hcsbot

# Build the React app
echo "📦 Building React app..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"

    # Restart PM2 frontend process
    echo "🔄 Restarting frontend..."
    pm2 restart hcsbot-frontend

    if [ $? -eq 0 ]; then
        echo "✅ Frontend restarted successfully!"
        echo ""
        echo "🎉 Deployment complete!"
        echo "💡 Clear browser cache or use: https://hcsbot.hcsonline.com/?v=$(date +%Y%m%d%H%M)"
    else
        echo "❌ Failed to restart frontend"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi
