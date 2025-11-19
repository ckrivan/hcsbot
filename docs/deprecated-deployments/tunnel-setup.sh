#!/bin/bash

echo "🌐 Setting up Cloudflare Tunnel for Backend API"
echo "============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}Option 1: Quick Temporary Tunnel${NC}"
echo "Run this command in a separate terminal:"
echo -e "${YELLOW}cloudflared tunnel --url http://localhost:8000${NC}"
echo ""
echo "This will give you a temporary URL like:"
echo "https://xyz-abc-def.trycloudflare.com"
echo ""
echo "Then you'll need to either:"
echo "1. Update your frontend to use this URL temporarily, OR"
echo "2. Set up a CNAME record: api.tektest.org -> xyz-abc-def.trycloudflare.com"
echo ""

echo -e "${BLUE}Option 2: Permanent Named Tunnel (Recommended)${NC}"
echo "1. Login to Cloudflare:"
echo -e "   ${YELLOW}cloudflared tunnel login${NC}"
echo ""
echo "2. Create a named tunnel:"
echo -e "   ${YELLOW}cloudflared tunnel create hcs-api${NC}"
echo ""
echo "3. Configure the tunnel to route api.tektest.org to localhost:8000"
echo -e "   ${YELLOW}cloudflared tunnel route dns hcs-api api.tektest.org${NC}"
echo ""
echo "4. Run the tunnel:"
echo -e "   ${YELLOW}cloudflared tunnel run hcs-api${NC}"
echo ""

echo -e "${BLUE}Current Status:${NC}"
echo "✅ Backend running at: http://localhost:8000"
echo "✅ Frontend expects API at: https://api.tektest.org"
echo "❌ Need to connect localhost:8000 -> api.tektest.org"
echo ""

echo -e "${YELLOW}Quick Test (try this first):${NC}"
echo "In a new terminal window, run:"
echo "cloudflared tunnel --url http://localhost:8000"
echo ""
echo "Then test the temporary URL it provides!"