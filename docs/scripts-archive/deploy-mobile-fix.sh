#!/bin/bash

echo "🔧 Mobile Fix Deployment for HCS Chatbot"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📱 Mobile Safari & Chrome Fix${NC}"
echo "Changes included:"
echo "- iOS Safari specific CORS headers"
echo "- Fetch fallback for mobile browsers"
echo "- Fixed PDF links to use production API"
echo "- Enhanced error debugging"
echo ""

# Build frontend
echo -e "${BLUE}🔨 Building frontend with production API URL...${NC}"
REACT_APP_API_URL=https://api.tektest.org npm run build
echo ""

# Check if build was successful
if [ ! -f "build/index.html" ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend build complete${NC}"
echo ""

# Instructions for backend
echo -e "${YELLOW}🚀 Backend Deployment Steps:${NC}"
echo ""
echo "1. Stop your current backend server"
echo ""
echo "2. Restart with the updated backend/app.py:"
echo "   cd backend && python app.py"
echo ""
echo "3. The backend now includes:"
echo "   - Mobile Safari compatibility middleware"
echo "   - Better CORS headers for iOS"
echo "   - Security headers"
echo ""

# Instructions for testing
echo -e "${YELLOW}🧪 Testing Steps:${NC}"
echo ""
echo "1. Deploy the 'build' folder to your web server"
echo ""
echo "2. Test on iPhone Safari:"
echo "   - Go to https://llm.tektest.org"
echo "   - Check console in Safari Web Inspector"
echo "   - Look for detailed error messages"
echo ""
echo "3. Debug mode (if needed):"
echo "   - Visit: https://llm.tektest.org?debug=true"
echo "   - Check browser console for detailed logs"
echo ""
echo "4. Test API directly on mobile:"
echo "   - Visit: https://api.tektest.org/health"
echo "   - Should return JSON response"
echo ""

echo -e "${GREEN}🎯 Key Changes for Mobile:${NC}"
echo "- allow_credentials=False (mobile compatibility)"
echo "- Added MobileCompatibilityMiddleware"
echo "- Fetch API fallback for iOS Safari"
echo "- Cache-Control headers for mobile browsers"
echo "- Debug info visible in error banner"
echo ""

echo -e "${BLUE}💡 If still not working:${NC}"
echo "1. Check Cloudflare SSL/TLS → Set to 'Full' or 'Full (strict)'"
echo "2. Clear Cloudflare cache completely"
echo "3. Try in private/incognito mode on mobile"
echo "4. Check mobile console for CORS or SSL errors"