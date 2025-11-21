#!/bin/bash

echo "🔍 HCS Chatbot - Production Deployment Verification"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# URLs
FRONTEND_URL="https://llm.tektest.org"
BACKEND_URL="https://api.tektest.org"

echo -e "${BLUE}🌐 Testing Production URLs...${NC}"
echo ""

# Test backend
echo -e "${YELLOW}Testing Backend API:${NC} $BACKEND_URL/health"
backend_response=$(curl -s "$BACKEND_URL/health" | head -c 200)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Backend is responding${NC}"
    echo "Response: $backend_response"
else
    echo -e "${RED}❌ Backend not responding${NC}"
fi

echo ""

# Test frontend HTML
echo -e "${YELLOW}Testing Frontend HTML:${NC} $FRONTEND_URL"
frontend_response=$(curl -s "$FRONTEND_URL" | head -c 500)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Frontend is responding${NC}"
    echo "Response preview: ${frontend_response:0:100}..."
else
    echo -e "${RED}❌ Frontend not responding${NC}"
fi

echo ""

# Check for JavaScript file references
echo -e "${BLUE}🔍 Checking JavaScript file references...${NC}"
js_file=$(curl -s "$FRONTEND_URL" | grep -o 'static/js/main\.[^"]*\.js' | head -1)
if [[ -n "$js_file" ]]; then
    echo "Found JS file: $js_file"
    
    # Check if the JS file contains localhost
    echo "Checking JS file for localhost references..."
    js_content=$(curl -s "$FRONTEND_URL/$js_file" 2>/dev/null)
    
    if echo "$js_content" | grep -q "localhost:8000"; then
        echo -e "${RED}❌ PROBLEM: JavaScript still contains localhost:8000${NC}"
        echo -e "${YELLOW}⚠️  The production site needs to be updated with the new build${NC}"
    else
        echo -e "${GREEN}✅ JavaScript does not contain localhost${NC}"
    fi
    
    if echo "$js_content" | grep -q "api.tektest.org"; then
        echo -e "${GREEN}✅ JavaScript contains production API URL${NC}"
    else
        echo -e "${RED}❌ JavaScript does not contain production API URL${NC}"
    fi
else
    echo -e "${RED}❌ Could not find JavaScript file reference${NC}"
fi

echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""

if [[ -n "$js_file" ]] && echo "$js_content" | grep -q "localhost:8000"; then
    echo -e "${YELLOW}🚨 ACTION REQUIRED:${NC}"
    echo "1. The production website is using an OLD version of the code"
    echo "2. You need to deploy the contents of your local 'build' folder"
    echo "3. Replace ALL files on your web server with the new build"
    echo ""
    echo -e "${BLUE}Deployment Steps:${NC}"
    echo "1. Upload the entire 'build' folder contents to your web server"
    echo "2. Make sure to replace the old JavaScript files"
    echo "3. Clear Cloudflare cache after deployment"
    echo "4. Hard refresh browser (Cmd+Shift+R)"
else
    echo -e "${GREEN}✅ Production site appears to be up to date${NC}"
    echo "The issue might be browser caching. Try:"
    echo "1. Clear Cloudflare cache"
    echo "2. Hard refresh browser (Cmd+Shift+R)"
    echo "3. Test in incognito/private mode"
fi

echo ""
echo -e "${YELLOW}Quick Fix Test:${NC}"
echo "Visit: $FRONTEND_URL?v=$(date +%s) (cache busting)"
echo "Or try: $FRONTEND_URL?debug=true (debug mode)"