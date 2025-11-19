#!/bin/bash

echo "🔄 Cloudflare Cache Purge Script"
echo "================================"
echo ""

# You'll need to set these variables
CLOUDFLARE_EMAIL="your-email@example.com"
CLOUDFLARE_API_KEY="your-global-api-key"
CLOUDFLARE_ZONE_ID="your-zone-id"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📋 To use this script, you need:${NC}"
echo "1. Your Cloudflare email"
echo "2. Global API Key (Account Settings → API Tokens → Global API Key)"
echo "3. Zone ID (Overview page of your domain in Cloudflare)"
echo ""

# Uncomment and fill in your details above, then uncomment below:

# Option 1: Purge everything
# echo -e "${YELLOW}Purging all cache...${NC}"
# curl -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
#      -H "X-Auth-Email: $CLOUDFLARE_EMAIL" \
#      -H "X-Auth-Key: $CLOUDFLARE_API_KEY" \
#      -H "Content-Type: application/json" \
#      --data '{"purge_everything":true}'

# Option 2: Purge specific files
# echo -e "${YELLOW}Purging specific files...${NC}"
# curl -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
#      -H "X-Auth-Email: $CLOUDFLARE_EMAIL" \
#      -H "X-Auth-Key: $CLOUDFLARE_API_KEY" \
#      -H "Content-Type: application/json" \
#      --data '{"files":["https://llm.tektest.org/hcs-logo.png","https://llm.tektest.org/static/css/main.2e5f2e65.css"]}'

echo -e "${GREEN}✅ Cache purge complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
echo "2. Check in incognito/private mode to avoid local cache"