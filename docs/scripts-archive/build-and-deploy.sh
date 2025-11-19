#!/bin/bash

echo "🚀 HCS Chatbot - Complete Build & Deploy Script"
echo "==============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PRODUCTION_API_URL="https://api.tektest.org"
FRONTEND_URL="https://llm.tektest.org"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "   Production API URL: $PRODUCTION_API_URL"
echo "   Frontend URL: $FRONTEND_URL"
echo ""

# Clean previous build
echo -e "${YELLOW}🧹 Cleaning previous build...${NC}"
rm -rf build/
echo ""

# Set environment and build
echo -e "${BLUE}🔨 Building with production settings...${NC}"
export NODE_ENV=production
export REACT_APP_API_URL="$PRODUCTION_API_URL"

echo "Environment check:"
echo "   NODE_ENV: $NODE_ENV"
echo "   REACT_APP_API_URL: $REACT_APP_API_URL"
echo ""

# Build the application
npm run build

# Verify build was successful
if [ ! -f "build/index.html" ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful!${NC}"
echo ""

# Verify the API URL is correct in the build
echo -e "${BLUE}🔍 Verifying API URL in build...${NC}"
if grep -r "localhost:8000" build/ --exclude="*.map" > /dev/null; then
    echo -e "${RED}❌ ERROR: localhost:8000 found in actual build files!${NC}"
    echo "The build still contains localhost URLs. Check environment variables."
    exit 1
else
    echo -e "${GREEN}✅ No localhost URLs found in build (excluding source maps)${NC}"
fi

# Check if production API URL is in the build
if grep -r "$PRODUCTION_API_URL" build/ > /dev/null; then
    echo -e "${GREEN}✅ Production API URL found in build${NC}"
else
    echo -e "${YELLOW}⚠️  Production API URL not found in build (may be minified)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Build Complete!${NC}"
echo ""

# Deployment instructions
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. 🖥️  Backend Deployment:"
echo "   - Ensure backend/app.py is updated with mobile fixes"
echo "   - Start: cd backend && python app.py"
echo "   - Should run on port 8000"
echo "   - Test: curl https://api.tektest.org/health"
echo ""
echo "2. 🌐 Frontend Deployment:"
echo "   - Deploy the 'build' folder contents to your web server"
echo "   - Configure Cloudflare tunnel to serve on $FRONTEND_URL"
echo "   - OR test locally: npx serve -s build -l 3000"
echo ""
echo "3. 📱 Mobile Testing:"
echo "   - Clear Cloudflare cache completely"
echo "   - Test on iPhone: $FRONTEND_URL"
echo "   - Test API directly: $PRODUCTION_API_URL/health"
echo "   - For debug info: $FRONTEND_URL?debug=true"
echo ""
echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "- PDF links should now use: $PRODUCTION_API_URL/pdf/filename.pdf"
echo "- Mobile connection should work with updated CORS"
echo "- Check browser console for detailed error messages"