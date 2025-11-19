#!/bin/bash

# Post-Deployment Test Script
# Verifies that HCSBot is correctly deployed and functioning

set -e

# Configuration
DOMAIN="hcsbot.hcsonline.com"
API_URL="https://${DOMAIN}/api"
FRONTEND_URL="https://${DOMAIN}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}HCSBot Deployment Tests${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: PM2 Services
print_test "Checking PM2 services..."
if pm2 list | grep -q "hcsbot-backend.*online" && pm2 list | grep -q "hcsbot-frontend.*online"; then
    print_pass "Both services are running"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Services are not running correctly"
    pm2 status
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 2: Nginx Status
print_test "Checking Nginx status..."
if systemctl is-active --quiet nginx; then
    print_pass "Nginx is active"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Nginx is not active"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 3: Backend Health
print_test "Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/health" 2>/dev/null | tail -1)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_pass "Backend health check passed (HTTP 200)"
    TESTS_PASSED=$((TESTS_PASSED + 1))

    # Check health details
    HEALTH_DATA=$(curl -s "${API_URL}/health" 2>/dev/null)
    echo "  Health data: $HEALTH_DATA"
else
    print_fail "Backend health check failed (HTTP $HEALTH_RESPONSE)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 4: Frontend Accessibility
print_test "Testing frontend accessibility..."
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" "${FRONTEND_URL}" 2>/dev/null | tail -1)
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    print_pass "Frontend accessible (HTTP 200)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Frontend not accessible (HTTP $FRONTEND_RESPONSE)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 5: SSL Certificate
print_test "Checking SSL certificate..."
if curl -s "https://${DOMAIN}" > /dev/null 2>&1; then
    CERT_EXPIRY=$(echo | openssl s_client -servername ${DOMAIN} -connect ${DOMAIN}:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    print_pass "SSL certificate valid until: $CERT_EXPIRY"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "SSL certificate check failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 6: Database Stats
print_test "Checking vector database..."
DB_STATS=$(curl -s "${API_URL}/database-stats" 2>/dev/null)
if [ -n "$DB_STATS" ]; then
    DOC_COUNT=$(echo $DB_STATS | grep -o '"total_documents":[0-9]*' | cut -d: -f2)
    if [ -n "$DOC_COUNT" ] && [ "$DOC_COUNT" -gt 0 ]; then
        print_pass "Vector database has $DOC_COUNT documents"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_fail "Vector database has no documents"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    print_fail "Could not retrieve database stats"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 7: Sample Questions
print_test "Testing sample questions endpoint..."
SAMPLES_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/sample-questions" 2>/dev/null | tail -1)
if [ "$SAMPLES_RESPONSE" = "200" ]; then
    print_pass "Sample questions endpoint working"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Sample questions endpoint failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 8: Ports Listening
print_test "Checking if required ports are listening..."
if netstat -tuln | grep -q ":8000 " && netstat -tuln | grep -q ":3000 "; then
    print_pass "Backend (8000) and frontend (3000) ports are listening"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Required ports are not listening"
    echo "  Port status:"
    netstat -tuln | grep -E ":(8000|3000) "
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 9: Log Files
print_test "Checking for error logs..."
if [ -f /var/log/nginx/hcsbot-error.log ]; then
    ERROR_COUNT=$(wc -l < /var/log/nginx/hcsbot-error.log)
    if [ "$ERROR_COUNT" -lt 10 ]; then
        print_pass "Minimal errors in Nginx logs ($ERROR_COUNT lines)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_fail "Many errors in Nginx logs ($ERROR_COUNT lines)"
        echo "  Recent errors:"
        tail -5 /var/log/nginx/hcsbot-error.log
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    print_fail "Nginx error log not found"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 10: DNS Resolution
print_test "Checking DNS resolution..."
RESOLVED_IP=$(dig +short ${DOMAIN} | tail -1)
if [ "$RESOLVED_IP" = "67.225.163.130" ]; then
    print_pass "DNS correctly resolves to 67.225.163.130"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "DNS resolves to $RESOLVED_IP (expected 67.225.163.130)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! Deployment successful.${NC}"
    echo -e "\nYour application is live at:"
    echo -e "  ${BLUE}https://${DOMAIN}${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please review the errors above.${NC}"
    echo -e "\nFor troubleshooting, check:"
    echo -e "  - PM2 logs: ${BLUE}pm2 logs${NC}"
    echo -e "  - Nginx logs: ${BLUE}sudo tail -f /var/log/nginx/hcsbot-error.log${NC}"
    echo -e "  - Service status: ${BLUE}pm2 status${NC}"
    exit 1
fi
