#!/bin/bash

# Pre-Deployment Check Script for HCSBot
# This script verifies that the server is ready for deployment

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Track issues
ERRORS=0
WARNINGS=0

print_header "HCSBot Pre-Deployment Checklist"

# Check 1: Operating System
print_check "Checking operating system..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" ]]; then
        print_success "Ubuntu detected ($VERSION)"
    else
        print_warning "OS is $ID - Ubuntu recommended"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_error "Cannot determine OS"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Python
print_check "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_error "Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: pip
print_check "Checking pip installation..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
    print_success "pip $PIP_VERSION detected"
else
    print_error "pip3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: Node.js
print_check "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)

    if [ "$NODE_MAJOR" -ge 18 ]; then
        print_success "Node.js $NODE_VERSION detected"
    else
        print_error "Node.js 18+ required, found $NODE_VERSION"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_error "Node.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: npm
print_check "Checking npm installation..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_success "npm $NPM_VERSION detected"
else
    print_error "npm not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: Nginx
print_check "Checking Nginx installation..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | cut -d'/' -f2)
    print_success "Nginx $NGINX_VERSION detected"
else
    print_warning "Nginx not installed (will be installed during deployment)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: PM2
print_check "Checking PM2 installation..."
if command -v pm2 &> /dev/null; then
    PM2_VERSION=$(pm2 --version)
    print_success "PM2 $PM2_VERSION detected"
else
    print_warning "PM2 not installed (will be installed during deployment)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 8: Git
print_check "Checking Git installation..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_success "Git $GIT_VERSION detected"
else
    print_error "Git not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 9: Disk Space
print_check "Checking disk space..."
AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -ge 20 ]; then
    print_success "${AVAILABLE_SPACE}GB available (20GB+ required)"
else
    print_error "Only ${AVAILABLE_SPACE}GB available (20GB+ required)"
    ERRORS=$((ERRORS + 1))
fi

# Check 10: Memory
print_check "Checking system memory..."
TOTAL_MEM=$(free -g | grep Mem | awk '{print $2}')
if [ "$TOTAL_MEM" -ge 4 ]; then
    print_success "${TOTAL_MEM}GB RAM available (4GB+ required)"
else
    print_warning "Only ${TOTAL_MEM}GB RAM (4GB+ recommended)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 11: Firewall
print_check "Checking firewall (UFW)..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | grep -i "Status:" | cut -d' ' -f2)
    print_success "UFW installed (Status: $UFW_STATUS)"
else
    print_warning "UFW not installed (will be configured during deployment)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 12: DNS Resolution
print_check "Checking DNS resolution for hcsbot.hcsonline.com..."
if command -v dig &> /dev/null; then
    DNS_IP=$(dig +short hcsbot.hcsonline.com | tail -1)
    if [ -n "$DNS_IP" ]; then
        if [ "$DNS_IP" == "67.225.163.130" ]; then
            print_success "DNS correctly points to 67.225.163.130"
        else
            print_warning "DNS points to $DNS_IP (expected 67.225.163.130)"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        print_warning "DNS not configured yet for hcsbot.hcsonline.com"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_warning "dig not installed, skipping DNS check"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 13: Port Availability
print_check "Checking port availability..."
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":8000 "; then
        print_warning "Port 8000 already in use"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "Port 8000 available"
    fi

    if netstat -tuln | grep -q ":3000 "; then
        print_warning "Port 3000 already in use"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "Port 3000 available"
    fi
else
    print_warning "netstat not available, skipping port check"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 14: .env file
print_check "Checking .env configuration..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
if [ -f "$REPO_ROOT/.env" ]; then
    print_success ".env file exists"

    # Check for required variables
    if grep -q "OPENAI_API_KEY=sk-" "$REPO_ROOT/.env"; then
        print_success "OpenAI API key configured"
    else
        print_error "OpenAI API key not configured in .env"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "LIQUIDWEB_API_USERNAME=" "$REPO_ROOT/.env"; then
        print_success "LiquidWeb credentials configured"
    else
        print_warning "LiquidWeb credentials not configured in .env"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_error ".env file not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 15: PDF Directory
print_check "Checking PDF directory..."
if [ -d "$REPO_ROOT/PDFs" ]; then
    PDF_COUNT=$(ls -1 "$REPO_ROOT/PDFs"/*.pdf 2>/dev/null | wc -l)
    if [ "$PDF_COUNT" -gt 0 ]; then
        print_success "$PDF_COUNT PDF files found"
    else
        print_warning "No PDF files in PDFs directory"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_warning "PDFs directory not found (will be created)"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
print_header "Pre-Deployment Check Summary"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
    echo -e "\nNext steps:"
    echo -e "  1. Review the configuration in .env"
    echo -e "  2. Run: ${BLUE}sudo ./deploy-liquidweb.sh${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Ready for deployment with $WARNINGS warning(s)${NC}"
    echo -e "\nYou can proceed with deployment:"
    echo -e "  ${BLUE}sudo ./deploy-liquidweb.sh${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS critical error(s) and $WARNINGS warning(s)${NC}"
    echo -e "\nPlease fix the errors before deploying."
    echo -e "\nFor detailed installation instructions, see:"
    echo -e "  ${BLUE}LIQUIDWEB-DEPLOYMENT.md${NC}"
    exit 1
fi
