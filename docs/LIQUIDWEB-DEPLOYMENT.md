# HCSBot LiquidWeb Deployment Guide

Complete deployment guide for hosting the HCS Apple Technology Chatbot on LiquidWeb infrastructure.

## 📋 Overview

- **Domain**: hcsbot.hcsonline.com
- **Server IP**: 67.225.163.130
- **Frontend**: React (port 3000)
- **Backend**: FastAPI (port 8000)
- **Database**: ChromaDB (local vector database)

## 🔑 Credentials

### LiquidWeb API
- **Username**: 4y484674ee8e6z5326u8
- **Token**: 985ee1baa7bb4d56d35548b9197488eac2811e22

### OpenAI
- **Provider**: OpenAI
- **Model**: gpt-4o-mini
- **API Key**: Configured in `.env` file

## 📦 Prerequisites

### Server Requirements
- **OS**: Ubuntu 22.04 LTS or newer
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 20GB minimum (40GB recommended)
- **CPU**: 2 vCores minimum (4 vCores recommended)

### Required Software
- Python 3.9+
- Node.js 18+
- Nginx
- PM2 (Process Manager)
- Certbot (for SSL)
- Git

## 🚀 Deployment Steps

### Step 1: DNS Configuration

Before deployment, ensure your domain points to your LiquidWeb server:

1. Log into your DNS management panel
2. Add/Update the following DNS record:
   ```
   Type: A
   Name: hcsbot
   Value: 67.225.163.130
   TTL: 3600
   ```
3. Wait for DNS propagation (5-30 minutes)
4. Verify: `dig hcsbot.hcsonline.com` or `nslookup hcsbot.hcsonline.com`

### Step 2: Server Access

SSH into your LiquidWeb server:

```bash
ssh root@67.225.163.130
```

### Step 3: Clone Repository

```bash
cd /opt
git clone https://github.com/ckrivan/hcsbot.git
cd hcsbot
```

### Step 4: Run Deployment Script

The automated deployment script will:
- Install all system dependencies
- Set up Python virtual environment
- Install Python packages
- Install Node.js packages
- Build the React frontend
- Configure PM2 process manager
- Set up Nginx reverse proxy
- Configure SSL with Let's Encrypt
- Set up firewall rules

Run the deployment:

```bash
sudo chmod +x deploy-liquidweb.sh
sudo ./deploy-liquidweb.sh
```

This script will take 10-15 minutes to complete.

### Step 5: Verify Environment Variables

The `.env` file should already be configured with:

```bash
cd /var/www/hcsbot
cat .env
```

Verify it contains:
- ✅ OPENAI_API_KEY
- ✅ OPENAI_MODEL=gpt-4o-mini
- ✅ LLM_PROVIDER=openai
- ✅ LIQUIDWEB_API_USERNAME
- ✅ LIQUIDWEB_API_TOKEN

### Step 6: Upload PDF Documents

Upload your Apple technology PDF documentation:

```bash
# From your local machine
scp -r /path/to/PDFs/* root@67.225.163.130:/var/www/hcsbot/PDFs/

# Or on the server
cd /var/www/hcsbot/PDFs
# Upload PDFs here
```

### Step 7: Initialize the Database

The system will automatically process PDFs on first run. To manually trigger initialization:

```bash
# Check if backend is running
pm2 status

# View backend logs
pm2 logs hcsbot-backend

# The system will process PDFs and create the vector database
# This may take 5-10 minutes depending on the number of PDFs
```

## ✅ Post-Deployment Verification

### Check Services

```bash
# Check PM2 processes
pm2 status

# Expected output:
# ┌─────┬──────────────────────┬─────────┬──────┐
# │ id  │ name                 │ status  │ cpu  │
# ├─────┼──────────────────────┼─────────┼──────┤
# │ 0   │ hcsbot-backend       │ online  │ 5%   │
# │ 1   │ hcsbot-frontend      │ online  │ 1%   │
# └─────┴──────────────────────┴─────────┴──────┘
```

### Check Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/hcsbot-access.log
```

### Check SSL Certificate

```bash
# Verify SSL certificate
sudo certbot certificates

# Test HTTPS
curl -I https://hcsbot.hcsonline.com
```

### Test Endpoints

```bash
# Test backend health
curl https://hcsbot.hcsonline.com/api/health

# Expected response:
# {"status":"healthy","initialized":true,"vector_db_healthy":true}

# Test frontend
curl -I https://hcsbot.hcsonline.com

# Expected: 200 OK
```

### Test in Browser

1. Open https://hcsbot.hcsonline.com
2. You should see the HCS Apple Technology Chatbot interface
3. Try asking a sample question
4. Verify you receive a response with sources

## 🔄 Updates and Maintenance

### Update Application Code

```bash
# SSH into server
ssh root@67.225.163.130

# Navigate to app directory
cd /var/www/hcsbot

# Activate virtual environment
source venv/bin/activate

# Pull latest changes
git pull origin main

# Update Python dependencies
pip install -r requirements.txt

# Update Node.js dependencies
npm install

# Rebuild frontend
npm run build:liquidweb

# Restart services
pm2 restart all

# Verify
pm2 status
```

### Update PDF Documents

```bash
# Add new PDFs
cd /var/www/hcsbot/PDFs
# Upload new PDFs

# Trigger reindexing via API
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```

### View Logs

```bash
# Backend logs
pm2 logs hcsbot-backend

# Frontend logs
pm2 logs hcsbot-frontend

# Nginx access logs
sudo tail -f /var/log/nginx/hcsbot-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/hcsbot-error.log
```

### Restart Services

```bash
# Restart all services
pm2 restart all

# Restart individual service
pm2 restart hcsbot-backend
pm2 restart hcsbot-frontend

# Reload Nginx
sudo systemctl reload nginx
```

## 🔧 Troubleshooting

### Backend Not Responding

```bash
# Check if backend is running
pm2 status

# Check backend logs for errors
pm2 logs hcsbot-backend --lines 100

# Restart backend
pm2 restart hcsbot-backend

# If issue persists, check Python dependencies
cd /var/www/hcsbot
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Frontend Not Loading

```bash
# Check if frontend service is running
pm2 status

# Rebuild frontend
cd /var/www/hcsbot
npm run build:liquidweb

# Restart frontend
pm2 restart hcsbot-frontend
```

### SSL Certificate Issues

```bash
# Renew SSL certificate manually
sudo certbot renew

# Force renew
sudo certbot renew --force-renewal

# Auto-renewal should be configured via cron
sudo certbot renew --dry-run
```

### Database Issues

```bash
# Check database stats
curl https://hcsbot.hcsonline.com/api/database-stats

# Reinitialize database
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'

# If database is corrupted, remove and rebuild
cd /var/www/hcsbot
rm -rf chroma_db
pm2 restart hcsbot-backend
# Wait for reinitialization (check logs)
```

### High Memory Usage

```bash
# Check system resources
htop

# Check PM2 memory usage
pm2 monit

# If ChromaDB is using too much memory, consider:
# 1. Reducing the number of PDFs
# 2. Increasing server RAM
# 3. Optimizing chunk size in pdf_processor.py
```

### Nginx 502 Bad Gateway

```bash
# Backend might not be running
pm2 status

# Check if ports are listening
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000

# Restart backend
pm2 restart hcsbot-backend

# Check Nginx error logs
sudo tail -f /var/log/nginx/hcsbot-error.log
```

## 🔒 Security Considerations

### Firewall Rules

```bash
# Check firewall status
sudo ufw status

# Should show:
# 22/tcp   ALLOW   (SSH)
# 80/tcp   ALLOW   (HTTP)
# 443/tcp  ALLOW   (HTTPS)
```

### API Key Protection

- ✅ API keys stored in `.env` file
- ✅ `.env` file NOT committed to git
- ✅ `.env` file has restricted permissions (600)
- ✅ API keys not exposed in logs

```bash
# Verify .env permissions
ls -la /var/www/hcsbot/.env
# Should show: -rw------- (600)

# If not, fix:
sudo chmod 600 /var/www/hcsbot/.env
```

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /var/www/hcsbot
source venv/bin/activate
pip list --outdated

# Update Node packages
npm outdated
```

## 📊 Monitoring

### Setup Monitoring (Optional)

Consider setting up monitoring with:
- **UptimeRobot**: Free uptime monitoring
- **PM2 Plus**: Advanced PM2 monitoring
- **CloudWatch**: If using AWS services

```bash
# Enable PM2 monitoring
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

### Performance Metrics

```bash
# CPU and Memory usage
pm2 monit

# Request metrics (from Nginx logs)
sudo tail -f /var/log/nginx/hcsbot-access.log | grep "POST /api/chat"
```

## 💰 Cost Estimation

### Monthly Costs

- **LiquidWeb VPS** (4 vCore, 8GB RAM): ~$25-50/month
- **OpenAI API** (gpt-4o-mini):
  - Light usage (100 queries/day): ~$0.50-1/month
  - Moderate usage (500 queries/day): ~$2.50-5/month
  - Heavy usage (2000 queries/day): ~$10-20/month
- **SSL Certificate**: Free (Let's Encrypt)
- **Domain**: Already owned

**Total**: ~$27-70/month depending on usage

## 📞 Support

For issues or questions:
- **Technical Issues**: Check logs first (`pm2 logs`)
- **LiquidWeb Support**: Available 24/7
- **OpenAI API Issues**: Check status.openai.com

## 📝 Quick Reference

### Common Commands

```bash
# SSH to server
ssh root@67.225.163.130

# Check services
pm2 status
pm2 logs
pm2 monit

# Restart all
pm2 restart all

# Update code
cd /var/www/hcsbot && git pull && npm run build:liquidweb && pm2 restart all

# View logs
pm2 logs hcsbot-backend
sudo tail -f /var/log/nginx/hcsbot-access.log

# Check SSL
sudo certbot certificates

# Test endpoints
curl https://hcsbot.hcsonline.com/api/health
```

---

**Deployed**: 2025-11-19
**Version**: 1.0.0
**Maintained by**: HCS Technology Group
