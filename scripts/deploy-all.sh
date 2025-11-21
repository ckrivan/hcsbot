#!/bin/bash

# Full Deployment Script for HCSBot
# This script rebuilds and restarts all components

echo "🚀 Starting full HCSBot deployment..."
echo ""

# Navigate to project directory
cd /var/www/hcsbot

# 1. Build the React frontend
echo "📦 Building React frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

echo "✅ Frontend build successful!"
echo ""

# 2. Restart all PM2 processes
echo "🔄 Restarting all services..."
pm2 restart all

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart services"
    exit 1
fi

echo "✅ All services restarted!"
echo ""

# 3. Show status
pm2 status

echo ""
echo "🎉 Deployment complete!"
echo "💡 Services: Backend, Frontend, Scraper"
echo "💡 Clear browser cache or use: https://hcsbot.hcsonline.com/?v=$(date +%Y%m%d%H%M)"
