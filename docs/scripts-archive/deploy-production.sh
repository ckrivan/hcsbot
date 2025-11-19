#!/bin/bash

echo "🚀 Production Deployment for HCS Apple Technology Chatbot"
echo "========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Build for production
echo -e "${BLUE}📦 Building for production...${NC}"
export REACT_APP_API_URL=https://api.tektest.org
npm run build

# Verify logo is in build
echo -e "${BLUE}🖼️  Verifying logo file...${NC}"
if [ -f "build/hcs-logo.png" ]; then
    echo -e "${GREEN}✅ Logo file found in build folder${NC}"
    ls -lh build/hcs-logo.png
else
    echo -e "${YELLOW}⚠️  Logo file not found, copying...${NC}"
    cp public/hcs-logo.png build/
fi

# Fix permissions
chmod 644 build/hcs-logo.png

echo ""
echo -e "${GREEN}✨ Build complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Deploy the 'build' folder to your web server"
echo "2. If using Cloudflare tunnel, make sure to:"
echo "   - Clear Cloudflare cache"
echo "   - Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)"
echo ""
echo "3. To serve locally for testing:"
echo "   npx serve -s build -l 3000"
echo ""
echo -e "${BLUE}🔍 Troubleshooting:${NC}"
echo "If logo still shows as white box:"
echo "- Check browser console for 404 errors"
echo "- Verify the file is accessible at: https://llm.tektest.org/hcs-logo.png"
echo "- Clear browser cache and Cloudflare cache"
echo "- Check if Cloudflare is caching the old version"