#!/bin/bash

echo "🔍 Deployment Status Check"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Local Build Status:${NC}"
echo "1. Checking local build files..."

# Check local build
if [ -f "build/index.html" ]; then
    echo -e "${GREEN}✅ Local build/index.html exists${NC}"
    
    # Check what API URL is in the local build
    if grep -q "api.tektest.org" build/static/js/*.js 2>/dev/null; then
        echo -e "${GREEN}✅ Local build contains production API URL${NC}"
    else
        echo -e "${RED}❌ Local build still has localhost${NC}"
    fi
else
    echo -e "${RED}❌ Local build folder not found${NC}"
    echo "Run: ./build-and-deploy.sh first"
fi

echo ""
echo -e "${BLUE}What needs to happen:${NC}"
echo ""
echo "1. 📁 Upload your LOCAL 'build' folder contents to your web server"
echo "   - This replaces the old files that contain localhost references"
echo ""
echo "2. 🌐 Your web server file structure should look like:"
echo "   ├── index.html"
echo "   ├── hcs-logo.png"
echo "   └── static/"
echo "       ├── css/main.d0c0554c.css"
echo "       └── js/main.11b33f8a.js"
echo ""
echo "3. 🧹 After uploading files:"
echo "   - Clear Cloudflare cache (Purge Everything)"
echo "   - Hard refresh browser"
echo ""

echo -e "${YELLOW}🚨 CRITICAL:${NC} The production website is serving OLD files"
echo "Until you replace them, users will see localhost errors."

echo ""
echo -e "${BLUE}Quick verification after deployment:${NC}"
echo "The error message should change from:"
echo -e "${RED}  'API endpoint: localhost:8000'${NC}"
echo "To:"
echo -e "${GREEN}  'API endpoint: https://api.tektest.org'${NC}"