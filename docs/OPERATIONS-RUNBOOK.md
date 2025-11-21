# HCSBot Operations Runbook

**System**: HCS Apple Technology Chatbot
**Environment**: Production - LiquidWeb
**Domain**: hcsbot.hcsonline.com
**Server IP**: 67.225.163.130
**Last Updated**: 2025-11-19

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Service Management](#service-management)
4. [Monitoring & Health Checks](#monitoring--health-checks)
5. [Log Management](#log-management)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Backup & Recovery](#backup--recovery)
9. [Security](#security)
10. [Emergency Contacts](#emergency-contacts)

---

## System Overview

### Purpose
RAG-powered chatbot providing expert assistance on Apple technology, Jamf Pro, and enterprise Apple device management for HCS Technology Group customers.

### Components
- **Frontend**: React SPA (served via PM2 on port 3000)
- **Backend**: FastAPI (Python) API server (port 8000)
- **Vector Database**: ChromaDB (local, persistent)
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt (auto-renewing)
- **Process Manager**: PM2
- **LLM Provider**: OpenAI (gpt-4o-mini)

### System Requirements
- **OS**: Ubuntu 24.04 LTS
- **RAM**: 8GB (4GB minimum)
- **Storage**: 50GB (20GB minimum)
- **Python**: 3.12+
- **Node.js**: 18.19+

---

## Architecture

```
Internet
    |
    v
┌─────────────────────────────────────┐
│  Nginx (Port 80/443)                │
│  SSL Termination                    │
│  Reverse Proxy                      │
└──────────────┬──────────────────────┘
               |
       ┌───────┴────────┐
       |                 |
       v                 v
┌──────────────┐  ┌──────────────────┐
│  Frontend    │  │  Backend API     │
│  PM2:3000    │  │  PM2:8000        │
│  React SPA   │  │  FastAPI         │
└──────────────┘  └────────┬─────────┘
                           |
                     ┌─────┴──────┬─────────┐
                     v            v         v
              ┌──────────┐  ┌─────────┐  ┌────────┐
              │ ChromaDB │  │ OpenAI  │  │ PDFs   │
              │ Vectors  │  │ API     │  │ Folder │
              └──────────┘  └─────────┘  └────────┘
```

### Directory Structure
```
/var/www/hcsbot/
├── backend/              # FastAPI application
│   ├── app.py           # Main application
│   ├── rag_system.py    # RAG implementation
│   ├── vector_db.py     # ChromaDB interface
│   └── pdf_processor.py # PDF extraction
├── build/               # React production build
├── PDFs/                # Source PDF documents (100 files)
├── chroma_db/           # Vector database (persistent)
├── venv/                # Python virtual environment
├── .env                 # Environment variables (SENSITIVE)
└── logs/                # Application logs
```

---

## Service Management

### Quick Reference Commands

| Action | Command |
|--------|---------|
| View all services | `pm2 status` |
| View logs | `pm2 logs` |
| Restart all | `pm2 restart all` |
| Stop all | `pm2 stop all` |
| Start all | `pm2 start all` |
| Monitor resources | `pm2 monit` |

### PM2 Services

#### 1. Backend Service (`hcsbot-backend`)

**Start:**
```bash
cd /var/www/hcsbot
pm2 start venv/bin/python --name hcsbot-backend \
  --interpreter none -- backend/app.py
```

**Status Check:**
```bash
pm2 status hcsbot-backend
pm2 logs hcsbot-backend --lines 50
```

**Environment:**
- Python 3.12 (virtual environment)
- Port: 8000
- Memory: ~1.5GB (during initialization), ~500MB (running)
- CPU: High during PDF processing, low during normal operation

#### 2. Frontend Service (`hcsbot-frontend`)

**Start:**
```bash
cd /var/www/hcsbot
pm2 serve build 3000 --name hcsbot-frontend --spa
```

**Status Check:**
```bash
pm2 status hcsbot-frontend
pm2 logs hcsbot-frontend --lines 50
```

**Environment:**
- Node.js 18.19
- Port: 3000
- Memory: ~60MB
- CPU: Low

### Nginx Service

**Commands:**
```bash
# Status
sudo systemctl status nginx

# Start/Stop/Restart
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# Reload configuration (no downtime)
sudo systemctl reload nginx

# Test configuration
sudo nginx -t
```

**Configuration:**
- Main config: `/etc/nginx/sites-available/hcsbot`
- Enabled: `/etc/nginx/sites-enabled/hcsbot`
- Logs: `/var/log/nginx/hcsbot-*.log`

---

## Monitoring & Health Checks

### Automated Monitoring

#### Health Endpoint
```bash
# Backend health check
curl https://hcsbot.hcsonline.com/api/health

# Expected response:
{
  "status": "healthy",          # or "unhealthy"
  "initialized": true,           # RAG system status
  "vector_db_healthy": true,     # Database status
  "database_stats": {
    "total_documents": 3276,
    "collection_name": "apple_pdfs",
    "db_path": "./chroma_db"
  }
}
```

#### Database Stats
```bash
curl https://hcsbot.hcsonline.com/api/database-stats
```

#### Sample Questions (Frontend Test)
```bash
curl https://hcsbot.hcsonline.com/api/sample-questions
```

### Manual Monitoring

#### Service Status
```bash
# PM2 services
pm2 status

# System resources
htop

# Disk usage
df -h /var/www/hcsbot

# Memory usage
free -h

# Network connections
netstat -tlnp | grep -E ":(8000|3000|80|443)"
```

#### Performance Metrics
```bash
# Real-time monitoring
pm2 monit

# Process details
pm2 show hcsbot-backend
pm2 show hcsbot-frontend
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Memory (Backend) | >2GB | >3GB | Restart backend |
| Memory (Frontend) | >100MB | >200MB | Restart frontend |
| Disk Usage | >80% | >90% | Clean logs/temp files |
| Response Time | >10s | >30s | Check API/database |
| Error Rate | >5% | >10% | Check logs immediately |

---

## Log Management

### PM2 Logs

**View Logs:**
```bash
# All services
pm2 logs

# Specific service
pm2 logs hcsbot-backend
pm2 logs hcsbot-frontend

# Last N lines
pm2 logs hcsbot-backend --lines 100

# Live tail
pm2 logs --raw

# No streaming (snapshot)
pm2 logs --nostream
```

**Log Locations:**
- Backend: `/root/.pm2/logs/hcsbot-backend-*.log`
- Frontend: `/root/.pm2/logs/hcsbot-frontend-*.log`

**Log Rotation:**
```bash
# Install log rotation
pm2 install pm2-logrotate

# Configure
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7       # Keep 7 days
pm2 set pm2-logrotate:compress true
```

### Nginx Logs

**Locations:**
- Access: `/var/log/nginx/hcsbot-access.log`
- Error: `/var/log/nginx/hcsbot-error.log`

**View Logs:**
```bash
# Recent errors
sudo tail -f /var/log/nginx/hcsbot-error.log

# Recent access
sudo tail -f /var/log/nginx/hcsbot-access.log

# Search for specific IP
sudo grep "192.168.1.100" /var/log/nginx/hcsbot-access.log

# Count requests by endpoint
sudo awk '{print $7}' /var/log/nginx/hcsbot-access.log | sort | uniq -c | sort -nr
```

### Application Logs

**Backend Logging Levels:**
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failures requiring attention

**Key Log Patterns:**
```bash
# Search for errors
pm2 logs hcsbot-backend --nostream | grep ERROR

# Search for specific user queries
pm2 logs hcsbot-backend --nostream | grep "Query:"

# Database operations
pm2 logs hcsbot-backend --nostream | grep "vector_db"

# OpenAI API calls
pm2 logs hcsbot-backend --nostream | grep "openai"
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Not Responding (502 Bad Gateway)

**Symptoms:**
- Frontend loads but API calls fail
- Nginx returns 502 error
- `curl https://hcsbot.hcsonline.com/api/health` fails

**Diagnosis:**
```bash
# Check if backend is running
pm2 status hcsbot-backend

# Check if port 8000 is listening
netstat -tlnp | grep :8000

# Check backend logs
pm2 logs hcsbot-backend --lines 100
```

**Solutions:**
```bash
# Restart backend
pm2 restart hcsbot-backend

# If still failing, check Python environment
cd /var/www/hcsbot
source venv/bin/activate
python backend/app.py  # Run manually to see errors

# Check dependencies
pip list | grep -E "fastapi|uvicorn|chromadb|openai"

# Reinstall if needed
pip install -r requirements.txt
```

#### 2. Frontend Not Loading

**Symptoms:**
- Blank page or 404 errors
- Build files missing

**Diagnosis:**
```bash
# Check frontend service
pm2 status hcsbot-frontend

# Check build directory
ls -la /var/www/hcsbot/build/

# Check Nginx configuration
sudo nginx -t
```

**Solutions:**
```bash
# Rebuild frontend
cd /var/www/hcsbot
npm run build:liquidweb

# Restart frontend service
pm2 restart hcsbot-frontend

# Reload Nginx
sudo systemctl reload nginx
```

#### 3. SSL Certificate Issues

**Symptoms:**
- HTTPS not working
- Certificate expired warnings
- Mixed content errors

**Diagnosis:**
```bash
# Check certificate status
sudo certbot certificates

# Check expiration
sudo certbot certificates | grep "Expiry Date"

# Test SSL
curl -I https://hcsbot.hcsonline.com
```

**Solutions:**
```bash
# Renew certificate manually
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Test auto-renewal
sudo certbot renew --dry-run
```

#### 4. High Memory Usage

**Symptoms:**
- System slowness
- Out of memory errors
- Services crashing

**Diagnosis:**
```bash
# Check memory usage
free -h
pm2 monit

# Check process memory
ps aux | grep -E "python|node" | sort -k4 -r
```

**Solutions:**
```bash
# Restart services
pm2 restart all

# Clear system cache
sudo sync && sudo sysctl -w vm.drop_caches=3

# If backend memory leak suspected
pm2 restart hcsbot-backend

# Check for runaway processes
top -o %MEM
```

#### 5. Database Issues

**Symptoms:**
- No search results
- "vector_db_healthy": false
- Documents not found

**Diagnosis:**
```bash
# Check database health
curl https://hcsbot.hcsonline.com/api/database-stats

# Check database directory
ls -lh /var/www/hcsbot/chroma_db/

# Check backend logs for database errors
pm2 logs hcsbot-backend | grep vector_db
```

**Solutions:**
```bash
# Reinitialize database (WARNING: Reprocesses all PDFs)
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'

# If database corrupted, backup and rebuild
cd /var/www/hcsbot
mv chroma_db chroma_db.backup.$(date +%Y%m%d)
pm2 restart hcsbot-backend
# Wait 5-10 minutes for reprocessing
```

#### 6. PDF Processing Failures

**Symptoms:**
- Low document count
- Missing content
- Processing errors in logs

**Diagnosis:**
```bash
# Check PDF count
ls -1 /var/www/hcsbot/PDFs/*.pdf | wc -l

# Check for corrupted PDFs
cd /var/www/hcsbot/PDFs
for pdf in *.pdf; do
    pdfinfo "$pdf" &>/dev/null || echo "Corrupted: $pdf"
done
```

**Solutions:**
```bash
# Remove corrupted PDFs
# (Move to backup first)

# Force reprocessing
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```

### Emergency Procedures

#### Complete Service Restart
```bash
# Stop all services
pm2 stop all
sudo systemctl stop nginx

# Wait 10 seconds
sleep 10

# Start services
sudo systemctl start nginx
pm2 start all

# Verify
pm2 status
sudo systemctl status nginx
curl https://hcsbot.hcsonline.com/api/health
```

#### System Reboot
```bash
# Save PM2 processes
pm2 save

# Reboot
sudo reboot

# After reboot, verify services
pm2 status
sudo systemctl status nginx
```

---

## Maintenance Procedures

### Daily Tasks

**Automated:**
- SSL certificate auto-renewal check (certbot timer)
- System log rotation

**Manual:**
```bash
# Quick health check
curl https://hcsbot.hcsonline.com/api/health

# Check service status
pm2 status

# Review error logs
pm2 logs --nostream | grep ERROR | tail -20
sudo tail -20 /var/log/nginx/hcsbot-error.log
```

### Weekly Tasks

```bash
# Review logs for issues
pm2 logs --nostream | grep ERROR | wc -l

# Check disk usage
df -h

# Check memory trends
free -h

# Review Nginx access patterns
sudo awk '{print $1}' /var/log/nginx/hcsbot-access.log | sort | uniq -c | sort -nr | head -20

# Check certificate expiration
sudo certbot certificates
```

### Monthly Tasks

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies (in staging first!)
cd /var/www/hcsbot
source venv/bin/activate
pip list --outdated

# Update Node packages (in staging first!)
npm outdated

# Review and clean old logs
sudo find /var/log/nginx/ -name "*.log.*" -mtime +30 -delete

# Backup database
cd /var/www/hcsbot
tar -czf backups/chroma_db_$(date +%Y%m%d).tar.gz chroma_db/

# Test disaster recovery
# (Document tested procedures)
```

### Quarterly Tasks

```bash
# Security audit
sudo apt list --upgradable
sudo ufw status

# Performance review
# - Check response times
# - Review resource usage trends
# - Capacity planning

# Update documentation
# - Review this runbook
# - Update procedures
# - Document new issues/solutions

# DR drill
# - Test backup restoration
# - Verify recovery procedures
```

---

## Backup & Recovery

### What to Backup

1. **Vector Database** (Critical)
   - Location: `/var/www/hcsbot/chroma_db/`
   - Size: ~500MB
   - Frequency: Daily

2. **Configuration Files** (Critical)
   - `.env` file (contains API keys)
   - Nginx configuration
   - PM2 ecosystem file

3. **Application Code** (Medium)
   - Should be in git repository
   - Local changes documented

4. **PDF Documents** (Low)
   - Stored separately, rarely change
   - Can be re-uploaded if needed

### Backup Procedures

#### Automated Daily Backup
```bash
#!/bin/bash
# /root/scripts/backup-hcsbot.sh

BACKUP_DIR="/backups/hcsbot"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup vector database
cd /var/www/hcsbot
tar -czf $BACKUP_DIR/chroma_db_$DATE.tar.gz chroma_db/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  .env \
  /etc/nginx/sites-available/hcsbot

# Backup PM2 configuration
pm2 save
cp /root/.pm2/dump.pm2 $BACKUP_DIR/pm2_$DATE.dump

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Upload to remote storage (optional)
# aws s3 sync $BACKUP_DIR s3://your-bucket/hcsbot-backups/
```

#### Setup Automated Backup
```bash
# Create backup script
sudo mkdir -p /root/scripts
sudo nano /root/scripts/backup-hcsbot.sh
# (Paste script above)
sudo chmod +x /root/scripts/backup-hcsbot.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /root/scripts/backup-hcsbot.sh") | crontab -
```

### Recovery Procedures

#### Restore Vector Database
```bash
# Stop backend
pm2 stop hcsbot-backend

# Backup current (if exists)
cd /var/www/hcsbot
mv chroma_db chroma_db.old

# Restore from backup
tar -xzf /backups/hcsbot/chroma_db_20250119.tar.gz

# Restart backend
pm2 start hcsbot-backend

# Verify
curl https://hcsbot.hcsonline.com/api/database-stats
```

#### Restore Configuration
```bash
# Extract backup
cd /tmp
tar -xzf /backups/hcsbot/config_20250119.tar.gz

# Restore .env
sudo cp .env /var/www/hcsbot/.env
sudo chmod 600 /var/www/hcsbot/.env

# Restore Nginx config
sudo cp hcsbot /etc/nginx/sites-available/
sudo nginx -t
sudo systemctl reload nginx
```

#### Complete System Recovery

**Scenario: Server failure, need to rebuild from scratch**

```bash
# 1. Provision new server
# 2. Install base requirements
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nodejs npm nginx git curl

# 3. Clone repository
cd /opt
git clone https://github.com/ckrivan/hcsbot.git
cd hcsbot

# 4. Restore configuration
tar -xzf /backups/hcsbot/config_YYYYMMDD.tar.gz
cp .env /opt/hcsbot/

# 5. Setup application
cp -r /opt/hcsbot /var/www/
cd /var/www/hcsbot

# 6. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:liquidweb

# 7. Restore vector database
tar -xzf /backups/hcsbot/chroma_db_YYYYMMDD.tar.gz

# 8. Setup PM2
npm install -g pm2
pm2 start venv/bin/python --name hcsbot-backend --interpreter none -- backend/app.py
pm2 serve build 3000 --name hcsbot-frontend --spa
pm2 save
pm2 startup

# 9. Configure Nginx
sudo cp nginx-liquidweb.conf /etc/nginx/sites-available/hcsbot
sudo ln -s /etc/nginx/sites-available/hcsbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 10. Setup SSL
sudo certbot --nginx -d hcsbot.hcsonline.com

# 11. Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 12. Verify
curl https://hcsbot.hcsonline.com/api/health
```

---

## Security

### Access Control

**SSH Access:**
- Port: 22
- Method: Key-based authentication only
- Users: root

**Firewall Rules:**
```bash
# View current rules
sudo ufw status numbered

# Current configuration:
# - Port 22 (SSH)
# - Port 80 (HTTP)
# - Port 443 (HTTPS)
# - All other ports blocked
```

### API Keys & Secrets

**Location:** `/var/www/hcsbot/.env`

**Permissions:**
```bash
# Verify secure permissions
ls -l /var/www/hcsbot/.env
# Should show: -rw------- (600)

# Fix if needed
sudo chmod 600 /var/www/hcsbot/.env
sudo chown root:root /var/www/hcsbot/.env
```

**Stored Secrets:**
- OPENAI_API_KEY
- LIQUIDWEB_API_USERNAME
- LIQUIDWEB_API_TOKEN

### SSL/TLS

**Certificate:**
- Provider: Let's Encrypt
- Type: Domain Validated (DV)
- Expiration: Auto-renews 30 days before expiry
- Location: `/etc/letsencrypt/live/hcsbot.hcsonline.com/`

**Renewal:**
```bash
# Check status
sudo certbot certificates

# Manual renewal
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

### Security Best Practices

1. **Regular Updates:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Monitor Failed Login Attempts:**
   ```bash
   sudo grep "Failed password" /var/log/auth.log | tail -20
   ```

3. **Review Nginx Access Logs:**
   ```bash
   sudo tail -100 /var/log/nginx/hcsbot-access.log
   ```

4. **Check for Suspicious Activity:**
   ```bash
   # Unusual API usage
   sudo awk '{print $1}' /var/log/nginx/hcsbot-access.log | sort | uniq -c | sort -nr | head -20

   # Large number of requests from single IP
   sudo grep "particular-ip" /var/log/nginx/hcsbot-access.log | wc -l
   ```

5. **Rotate API Keys Quarterly:**
   - Update OpenAI key
   - Update .env file
   - Restart services

---

## Known Issues

### Issue 1: RAG System Initialization Error

**Status:** Open
**Severity:** Medium
**Impact:** Chatbot functionality may be degraded

**Symptoms:**
- Health endpoint shows `"initialized": false`
- Error in logs: `"Client.__init__() got an unexpected keyword argument 'proxies'"`
- Vector database works correctly (3,276 documents)

**Workaround:**
- System is operational
- Database queries work
- Issue appears to be with OpenAI client initialization

**Investigation Notes:**
- OpenAI library version: 1.50.0
- No 'proxies' parameter found in code
- May be internal library version conflict
- ChromaDB telemetry errors (non-critical)

**Next Steps:**
1. Test with different OpenAI library versions
2. Check for cached/compiled Python modules
3. Review dependency tree for conflicts
4. Consider upgrading ChromaDB if OpenAI incompatibility

**Monitoring:**
```bash
# Check if issue resolves after restart
pm2 restart hcsbot-backend
sleep 30
curl https://hcsbot.hcsonline.com/api/health | jq '.initialized'
```

### Issue 2: ChromaDB Telemetry Errors

**Status:** Known, Non-Critical
**Severity:** Low
**Impact:** None (cosmetic log errors)

**Symptoms:**
- Frequent errors: `"Failed to send telemetry event"`
- Does not affect functionality

**Workaround:**
- Ignore these errors
- They do not impact database operations

---

## Emergency Contacts

### Internal Team
- **Primary Contact:** HCS Technology Group IT Team
- **Email:** support@hcsonline.com
- **Phone:** [Add phone number]

### External Services
- **LiquidWeb Support:** Available 24/7
  - Portal: manage.liquidweb.com
  - Phone: [Add support number]

- **OpenAI Support:**
  - Status: status.openai.com
  - Support: help.openai.com

### Escalation Path
1. **Level 1:** Check this runbook, attempt standard fixes
2. **Level 2:** Review logs, consult documentation
3. **Level 3:** Contact HCS IT Team
4. **Level 4:** Engage LiquidWeb support (infrastructure)
5. **Level 5:** OpenAI support (API issues)

---

## Appendix

### Useful Commands Cheat Sheet

```bash
# Quick status check
pm2 status && sudo systemctl status nginx

# Full health check
curl https://hcsbot.hcsonline.com/api/health | jq

# Restart everything
pm2 restart all && sudo systemctl reload nginx

# View all logs
pm2 logs

# Check disk and memory
df -h && free -h

# Monitor in real-time
pm2 monit

# Check ports
netstat -tlnp | grep -E ":(8000|3000|80|443)"

# Test DNS
dig hcsbot.hcsonline.com

# Check SSL
sudo certbot certificates

# Check firewall
sudo ufw status

# System resource usage
htop
```

### Environment Variables Reference

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# LLM Provider
LLM_PROVIDER=openai

# Optional LLM settings
USE_LOCAL_LLM=false
USE_OLLAMA=false

# LiquidWeb Configuration
LIQUIDWEB_API_USERNAME=4y484674ee8e6z5326u8
LIQUIDWEB_API_TOKEN=985ee1baa7bb4d56d35548b9197488eac2811e22

# Server Configuration
SERVER_IP=67.225.163.130
DOMAIN=hcsbot.hcsonline.com

# Database Paths
CHROMA_DB_PATH=./chroma_db
PDF_FOLDER_PATH=./PDFs
```

### Port Reference

| Port | Service | Protocol | Access |
|------|---------|----------|--------|
| 22 | SSH | TCP | External |
| 80 | HTTP (redirects to 443) | TCP | External |
| 443 | HTTPS (Nginx) | TCP | External |
| 3000 | Frontend (PM2) | TCP | Local only |
| 8000 | Backend (FastAPI) | TCP | Local only |

### File Permissions Reference

```bash
# Application directory
/var/www/hcsbot/                    755 root:root

# Sensitive files
/var/www/hcsbot/.env                600 root:root

# Python virtual environment
/var/www/hcsbot/venv/               755 root:root

# Database directory
/var/www/hcsbot/chroma_db/          755 root:root

# PDF directory
/var/www/hcsbot/PDFs/               755 root:root

# Nginx configuration
/etc/nginx/sites-available/hcsbot   644 root:root

# SSL certificates
/etc/letsencrypt/                   755 root:root
```

---

## Recent Updates & Enhancements

### 2025-11-19: Performance & Feature Improvements

#### 1. Acronym Expansion System
**Feature:** Automatic expansion of common Apple/Jamf acronyms in user queries

**Implementation:** `/var/www/hcsbot/backend/rag_system.py`
- 29 supported acronyms (ADE, ABM, APNS, DEP, MDM, VPP, PPPC, TCC, SCEP, etc.)
- Queries like "how do i setup ade?" automatically expand to "Automated Device Enrollment"
- Improves search accuracy for acronym-based queries

**Technical Details:**
```python
# Located in RAGSystem class
ACRONYM_MAP = {
    'ade': 'Automated Device Enrollment',
    'abm': 'Apple Business Manager',
    'apns': 'Apple Push Notification Service',
    # ... 26 more acronyms
}
```

#### 2. Recency Disclaimer for Post-2023 Queries
**Feature:** Automatic disclaimer for queries about recent software versions

**Implementation:** `/var/www/hcsbot/backend/rag_system.py`
- Detects mentions of 2024+ years, macOS Sequoia, iOS 18+, recent Jamf versions
- Appends disclaimer recommending vendor documentation for latest information
- Keeps users informed about documentation limitations

**Triggers:**
- Years: 2024, 2025, etc.
- macOS: Sequoia, macOS 15
- iOS: iOS 18, iOS 19, iPadOS 18+
- Jamf Pro: 11.5+, 12.x+

**Example Disclaimer:**
```
⚠️ Important Note: Our documentation was created prior to 2024.
If you're asking about recent software versions, features, or
configurations released after 2023, the information above may
not reflect the latest changes.

We recommend:
- Consult the official vendor documentation
- Check Apple's official support pages
- Review Jamf's release notes
```

#### 3. PDF Page Linking Fix
**Feature:** Direct navigation to specific PDF pages from source links

**Implementation:** `/var/www/hcsbot/src/App.js:526`
- Changed: `href=".../${filename}"`
- To: `href=".../${filename}#page=${page_number}"`
- Users now jump directly to the cited page instead of page 1

**Example:**
- Before: Click "Page 4 ↗" → Opens PDF at page 1
- After: Click "Page 4 ↗" → Opens PDF at page 4

#### 4. Response Time Optimization
**Change:** Reduced max_tokens from 1000 to 600

**Results:**
- Response time: 15.4s → 6.2s (60% improvement)
- Still provides comprehensive answers
- Better user experience

**Timing Breakdown:**
- Acronym expansion: <0.01s
- Vector search: 0.08-0.17s
- OpenAI API: ~6s
- Total: ~6.2s

**Configuration:** `/var/www/hcsbot/backend/rag_system.py:167`

#### 5. Directory Cleanup & Organization
**Change:** Moved non-essential files to `docs/` archive

**Structure:**
```
/var/www/hcsbot/
├── docs/
│   ├── deprecated-deployments/    # Cloudflare, Vercel, Docker configs
│   ├── scripts-archive/           # Old deployment scripts
│   └── old-api-implementation/    # Legacy API code
├── backend/                       # Active Python backend
├── src/                          # Active React frontend
├── PDFs/                         # Documentation (101 files)
├── chroma_db/                    # Vector database (3,276 chunks)
├── .env                          # Configuration (gitignored)
├── deploy-liquidweb.sh          # Primary deployment script
├── OPERATIONS-RUNBOOK.md        # This file
└── requirements.txt             # Python dependencies
```

**Benefits:**
- Cleaner root directory
- Easier navigation
- Better maintainability
- Preserved historical configs for reference

#### 6. Git Integration
**Added:**
- `.gitignore` file excluding sensitive/large files
- Repository initialized in `/var/www/hcsbot/`
- Branch: `liquid-web-hcsbot`
- Remote: https://github.com/ckrivan/hcsbot.git

**Ignored Files:**
```
.env (API keys)
node_modules/ (dependencies)
venv/ (Python environment)
chroma_db/ (database)
PDFs/ (large files)
build/ (compiled output)
feedback.json (user data)
```

### Performance Metrics

**Current System Performance:**
- **RAM Usage:** 1.6GB / 8.1GB (20%)
  - Backend: 883MB
  - Frontend: 57MB
- **Response Time:** 6-7 seconds average
- **Database:** 3,276 searchable chunks from 101 PDFs
- **Uptime:** Auto-restart on failure (PM2)

**System Health:**
```bash
# Check current performance
curl https://hcsbot.hcsonline.com/api/database-stats

# Expected output:
{
  "total_documents": 3276,
  "collection_name": "apple_docs",
  "embedding_function": "all-MiniLM-L6-v2"
}
```

### Deployment Checklist

After making code changes:
1. ✅ Update backend: Edit Python files in `/var/www/hcsbot/backend/`
2. ✅ Update frontend: Edit React files in `/var/www/hcsbot/src/`
3. ✅ Rebuild frontend: `npm run build:liquidweb` (if frontend changed)
4. ✅ Restart services: `pm2 restart hcsbot-backend hcsbot-frontend`
5. ✅ Test functionality: Query chatbot with test questions
6. ✅ Update runbook: Document changes in this section
7. ✅ Commit to git: `git add -A && git commit -m "Description"`
8. ✅ Push to remote: `git push origin liquid-web-hcsbot`

---

**Document Version:** 1.1
**Created:** 2025-11-19
**Last Updated:** 2025-11-19 21:30 UTC
**Next Review:** 2025-12-19

---

*This runbook is a living document. Please update it when procedures change or new issues are discovered.*
