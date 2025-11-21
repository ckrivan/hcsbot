#!/bin/bash

# HCSBot Deployment Script for LiquidWeb
# This script deploys the HCS Apple Technology Chatbot to LiquidWeb hosting

set -e  # Exit on any error

echo "🚀 Starting HCSBot deployment to LiquidWeb..."

# Configuration
APP_NAME="hcsbot"
DOMAIN="hcsbot.hcsonline.com"
APP_DIR="/var/www/${APP_NAME}"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script with sudo or as root"
    exit 1
fi

# Step 1: Install system dependencies
print_status "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git curl

# Install PM2 globally
npm install -g pm2

print_success "System dependencies installed"

# Step 2: Create application directory
print_status "Setting up application directory..."
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# Step 3: Clone or copy repository (assuming we're running from the repo)
print_status "Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
rsync -av --exclude='node_modules' --exclude='build' --exclude='chroma_db' --exclude='.git' --exclude='backups' ${REPO_ROOT}/ ${APP_DIR}/

print_success "Application files copied"

# Step 4: Set up Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_success "Python dependencies installed"

# Step 5: Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install

print_success "Node.js dependencies installed"

# Step 6: Build React frontend
print_status "Building React frontend..."
npm run build:liquidweb

print_success "Frontend built successfully"

# Step 7: Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ${APP_DIR}/chroma_db
mkdir -p ${APP_DIR}/PDFs
mkdir -p ${APP_DIR}/logs

print_success "Directories created"

# Step 8: Set up PM2 for backend
print_status "Setting up PM2 for backend..."
pm2 delete ${APP_NAME}-backend 2>/dev/null || true
pm2 start ${APP_DIR}/venv/bin/python --name ${APP_NAME}-backend --interpreter none -- ${APP_DIR}/backend/app.py
pm2 save
pm2 startup systemd -u root --hp /root

print_success "Backend service configured with PM2"

# Step 9: Set up PM2 for frontend
print_status "Setting up PM2 for frontend..."
pm2 delete ${APP_NAME}-frontend 2>/dev/null || true
pm2 serve ${APP_DIR}/build ${FRONTEND_PORT} --name ${APP_NAME}-frontend --spa
pm2 save

print_success "Frontend service configured with PM2"

# Step 10: Configure Nginx
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/${APP_NAME} <<EOF
# Backend API server
server {
    listen 80;
    server_name ${DOMAIN};

    # Increased buffer sizes for large requests
    client_max_body_size 50M;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;

    # Logging
    access_log /var/log/nginx/${APP_NAME}-access.log;
    error_log /var/log/nginx/${APP_NAME}-error.log;

    # API endpoint
    location /api/ {
        proxy_pass http://localhost:${BACKEND_PORT}/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;

        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }

    # Frontend
    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;

        # Try files first, fallback to index for SPA
        try_files \$uri \$uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/

# Test Nginx configuration
print_status "Testing Nginx configuration..."
nginx -t

# Reload Nginx
print_status "Reloading Nginx..."
systemctl reload nginx

print_success "Nginx configured successfully"

# Step 11: Set up SSL with Let's Encrypt
print_status "Setting up SSL certificate..."
certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@hcsonline.com --redirect || {
    print_error "SSL certificate setup failed. You may need to run certbot manually."
}

# Step 12: Set up firewall
print_status "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_success "Firewall configured"

# Step 13: Set correct permissions
print_status "Setting permissions..."
chown -R www-data:www-data ${APP_DIR}
chmod -R 755 ${APP_DIR}

print_success "Permissions set"

# Print status
print_status "Checking service status..."
pm2 status

echo ""
print_success "🎉 Deployment completed successfully!"
echo ""
print_status "Your application is now running at:"
echo "  Frontend: https://${DOMAIN}"
echo "  Backend API: https://${DOMAIN}/api"
echo ""
print_status "To manage services:"
echo "  pm2 status              - Check service status"
echo "  pm2 logs                - View logs"
echo "  pm2 restart all         - Restart services"
echo "  pm2 stop all            - Stop services"
echo ""
print_status "To reload the application after updates:"
echo "  cd ${APP_DIR}"
echo "  git pull"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  npm install"
echo "  npm run build:liquidweb"
echo "  pm2 restart all"
echo ""
