# HCSBot LiquidWeb Deployment Checklist

Use this checklist to ensure a smooth deployment to your LiquidWeb hosting.

## ✅ Pre-Deployment Checklist

### 1. DNS Configuration
- [ ] Log into your DNS management panel
- [ ] Create A record: `hcsbot` pointing to `67.225.163.130`
- [ ] Wait 5-30 minutes for DNS propagation
- [ ] Verify with: `dig hcsbot.hcsonline.com`
- [ ] Confirm it returns: `67.225.163.130`

### 2. Server Access
- [ ] Can SSH to server: `ssh root@67.225.163.130`
- [ ] Server has Ubuntu 22.04 LTS (or compatible)
- [ ] Have sudo/root access

### 3. Credentials Ready
- [ ] OpenAI API Key configured in `.env` ✅
- [ ] LiquidWeb API credentials in `.env` ✅
- [ ] Domain correctly set in `.env` ✅

### 4. Application Files
- [ ] Repository cloned or files uploaded to server
- [ ] `.env` file present with correct values ✅
- [ ] PDFs uploaded to `/PDFs` directory (optional but recommended)
- [ ] All scripts are executable (`chmod +x *.sh`)

## 📋 Deployment Steps

### Step 1: Initial Setup
```bash
# SSH to server
ssh root@67.225.163.130

# Clone repository (if not already done)
cd /opt
git clone https://github.com/ckrivan/hcsbot.git
cd hcsbot

# Or upload your configured version
# scp -r hcsbot/ root@67.225.163.130:/opt/
```
- [ ] Repository files on server
- [ ] In correct directory (`/opt/hcsbot` or `/var/www/hcsbot`)

### Step 2: Pre-Deployment Check
```bash
chmod +x pre-deployment-check.sh
sudo ./pre-deployment-check.sh
```
- [ ] All checks passed (or acceptable warnings only)
- [ ] Python 3.9+ available
- [ ] Node.js 18+ available
- [ ] Sufficient disk space (20GB+)
- [ ] Sufficient RAM (4GB+)

### Step 3: Run Deployment
```bash
chmod +x deploy-liquidweb.sh
sudo ./deploy-liquidweb.sh
```
- [ ] Script started without errors
- [ ] System dependencies installed
- [ ] Python packages installed
- [ ] Node packages installed
- [ ] Frontend built successfully
- [ ] PM2 configured
- [ ] Nginx configured
- [ ] SSL certificate obtained
- [ ] Firewall configured

**Expected duration**: 15-20 minutes

### Step 4: Upload PDFs (if not done)
```bash
# From local machine
scp -r /path/to/PDFs/*.pdf root@67.225.163.130:/var/www/hcsbot/PDFs/

# Or on server
cd /var/www/hcsbot/PDFs
# Upload PDFs manually
```
- [ ] PDFs uploaded to server
- [ ] PDFs in correct directory: `/var/www/hcsbot/PDFs/`

### Step 5: Verify Services
```bash
# Check PM2 status
pm2 status

# Check Nginx
sudo systemctl status nginx
sudo nginx -t
```
- [ ] `hcsbot-backend` status: `online`
- [ ] `hcsbot-frontend` status: `online`
- [ ] Nginx status: `active (running)`
- [ ] Nginx config test: `successful`

### Step 6: Test Deployment
```bash
chmod +x test-deployment.sh
sudo ./test-deployment.sh
```
- [ ] All tests passed
- [ ] Backend health check: ✅
- [ ] Frontend accessible: ✅
- [ ] SSL certificate valid: ✅
- [ ] Database initialized: ✅

### Step 7: Browser Testing
Visit `https://hcsbot.hcsonline.com`:
- [ ] Page loads without errors
- [ ] Chat interface visible
- [ ] Sample questions displayed
- [ ] Can send a test message
- [ ] Receive response with sources
- [ ] No console errors (F12 Developer Tools)

## 🔍 Verification Checklist

### Service Status
```bash
pm2 status
```
Expected output:
```
┌─────┬──────────────────────┬─────────┬──────┐
│ id  │ name                 │ status  │ cpu  │
├─────┼──────────────────────┼─────────┼──────┤
│ 0   │ hcsbot-backend       │ online  │ 5%   │
│ 1   │ hcsbot-frontend      │ online  │ 1%   │
└─────┴──────────────────────┴─────────┴──────┘
```
- [ ] Both services showing `online`
- [ ] CPU usage reasonable (<50%)
- [ ] Memory usage acceptable

### Endpoint Testing
```bash
# Backend health
curl https://hcsbot.hcsonline.com/api/health

# Frontend
curl -I https://hcsbot.hcsonline.com

# Database stats
curl https://hcsbot.hcsonline.com/api/database-stats
```
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] Frontend returns `HTTP/2 200`
- [ ] Database has documents loaded

### SSL/HTTPS
```bash
sudo certbot certificates
```
- [ ] Certificate issued for `hcsbot.hcsonline.com`
- [ ] Certificate valid (not expired)
- [ ] Auto-renewal configured

### Logs Check
```bash
# PM2 logs
pm2 logs --lines 20

# Nginx logs
sudo tail -20 /var/log/nginx/hcsbot-access.log
sudo tail -20 /var/log/nginx/hcsbot-error.log
```
- [ ] No critical errors in PM2 logs
- [ ] Backend initialized successfully
- [ ] PDFs processed (if uploaded)
- [ ] Minimal errors in Nginx logs

## 🎯 Final Verification

### Functional Testing
Test these features in the browser:

1. **Basic Chat**
   - [ ] Ask: "How do I deploy Zoom using Jamf Pro?"
   - [ ] Receive relevant answer with sources
   - [ ] Sources show PDF name and page number

2. **Sample Questions**
   - [ ] Sample questions are displayed
   - [ ] Can click on a sample question
   - [ ] Question is sent to chat
   - [ ] Receive appropriate response

3. **Smart Suggestions**
   - [ ] Try typing just "Jamf Connect"
   - [ ] System offers specific questions
   - [ ] Can click suggested questions

4. **Admin Access** (if needed)
   - [ ] Admin login works
   - [ ] Can view feedback
   - [ ] Feedback storage persists

### Performance Testing
- [ ] Response time reasonable (<10 seconds)
- [ ] No timeout errors
- [ ] Multiple queries work consecutively
- [ ] Sources are accurate and relevant

## 📊 Monitoring Setup (Optional but Recommended)

### PM2 Monitoring
```bash
# Set up log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```
- [ ] Log rotation configured
- [ ] Logs won't fill up disk space

### Uptime Monitoring
Consider setting up:
- [ ] UptimeRobot (free tier available)
- [ ] Pingdom
- [ ] StatusCake

Monitor URL: `https://hcsbot.hcsonline.com/api/health`

## 🚨 Troubleshooting Checklist

If something isn't working:

### Services Not Running
```bash
pm2 logs
pm2 restart all
pm2 status
```
- [ ] Check logs for errors
- [ ] Restart services
- [ ] Verify both services start successfully

### Backend Errors
```bash
cd /var/www/hcsbot
source venv/bin/activate
python backend/app.py
```
- [ ] Run backend manually to see errors
- [ ] Check for missing dependencies
- [ ] Verify API key in `.env`

### Frontend Not Loading
```bash
cd /var/www/hcsbot
npm run build:liquidweb
pm2 restart hcsbot-frontend
```
- [ ] Rebuild frontend
- [ ] Check for build errors
- [ ] Verify static files exist in `build/`

### Database Issues
```bash
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```
- [ ] Force database reinitialization
- [ ] Check PDFs directory has files
- [ ] Verify PDFs are readable

### SSL Issues
```bash
sudo certbot renew --dry-run
sudo certbot certificates
```
- [ ] Certificate is valid
- [ ] Auto-renewal is working

## ✅ Post-Deployment Tasks

### Documentation
- [ ] Save deployment date and time
- [ ] Document any custom changes made
- [ ] Note PDF count and topics covered
- [ ] Record expected query volume

### Team Communication
- [ ] Notify team that chatbot is live
- [ ] Share URL: `https://hcsbot.hcsonline.com`
- [ ] Provide usage guidelines
- [ ] Set up support process

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure alert emails
- [ ] Create dashboard (optional)
- [ ] Schedule regular checks

### Maintenance Schedule
- [ ] Weekly: Check logs and service status
- [ ] Monthly: Update dependencies
- [ ] Monthly: Review and update PDFs
- [ ] Quarterly: Review SSL certificate
- [ ] As needed: Scale server if required

## 📝 Deployment Notes

**Deployment Date**: _______________

**Deployed By**: _______________

**Server**: 67.225.163.130

**Domain**: hcsbot.hcsonline.com

**Initial PDF Count**: _______________

**Notes**:
_________________________________
_________________________________
_________________________________

## ✨ Success Criteria

Deployment is successful when:
- ✅ All services running (`pm2 status`)
- ✅ HTTPS working with valid certificate
- ✅ Frontend loads in browser
- ✅ Backend health check passes
- ✅ Chat functionality works
- ✅ Responses include source citations
- ✅ No critical errors in logs
- ✅ Performance is acceptable (<10s response)

---

**Congratulations! Your HCSBot is now live at https://hcsbot.hcsonline.com 🎉**

For ongoing maintenance, refer to:
- `LIQUIDWEB-DEPLOYMENT.md` - Full deployment guide
- `QUICKSTART-LIQUIDWEB.md` - Quick reference
- `test-deployment.sh` - Automated testing
