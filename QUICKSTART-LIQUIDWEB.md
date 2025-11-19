# HCSBot LiquidWeb - Quick Start Guide

## 🎯 One-Command Deployment

After setting up DNS and accessing your server, deployment is simple:

```bash
# 1. Clone repository
git clone https://github.com/ckrivan/hcsbot.git
cd hcsbot

# 2. Run pre-deployment check
chmod +x pre-deployment-check.sh
sudo ./pre-deployment-check.sh

# 3. Deploy (if checks pass)
sudo ./deploy-liquidweb.sh
```

That's it! The script handles everything automatically.

## 📋 Before You Start

### 1. DNS Setup (Do This First!)
Point your domain to your server:
```
Type: A Record
Name: hcsbot
Value: 67.225.163.130
TTL: 3600
```

Verify: `dig hcsbot.hcsonline.com` should return `67.225.163.130`

### 2. Server Access
```bash
ssh root@67.225.163.130
```

### 3. Required Information
All credentials are already configured in the `.env` file:
- ✅ OpenAI API Key
- ✅ LiquidWeb API credentials
- ✅ Domain configuration

## 🚀 Deployment Process

The deployment script automatically:

1. **Installs Dependencies** (5 min)
   - Python 3.9+
   - Node.js 18+
   - Nginx
   - PM2
   - Certbot

2. **Builds Application** (5 min)
   - Sets up Python virtual environment
   - Installs Python packages
   - Builds React frontend

3. **Configures Services** (2 min)
   - PM2 process manager
   - Nginx reverse proxy
   - SSL certificate (HTTPS)
   - Firewall rules

**Total Time**: ~15 minutes

## ✅ Verification

After deployment, test these endpoints:

```bash
# Health check
curl https://hcsbot.hcsonline.com/api/health

# Frontend
curl -I https://hcsbot.hcsonline.com

# Check services
pm2 status
```

Open in browser: **https://hcsbot.hcsonline.com**

## 📁 File Structure

```
/var/www/hcsbot/          # Application root
├── backend/              # FastAPI backend
├── build/                # React build (production)
├── PDFs/                 # Documentation files
├── chroma_db/            # Vector database
├── .env                  # Environment variables
└── venv/                 # Python virtual environment
```

## 🔄 Common Tasks

### Update Application
```bash
cd /var/www/hcsbot
git pull
source venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:liquidweb
pm2 restart all
```

### View Logs
```bash
pm2 logs                  # All logs
pm2 logs hcsbot-backend   # Backend only
pm2 logs hcsbot-frontend  # Frontend only
```

### Restart Services
```bash
pm2 restart all           # Restart everything
pm2 restart hcsbot-backend
pm2 restart hcsbot-frontend
```

### Add PDFs
```bash
# Upload PDFs to server
scp my-doc.pdf root@67.225.163.130:/var/www/hcsbot/PDFs/

# Reindex
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```

## 🔧 Troubleshooting

### Service Not Running
```bash
pm2 status
pm2 restart all
pm2 logs
```

### Nginx Issues
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/hcsbot-error.log
```

### Database Issues
```bash
# Check status
curl https://hcsbot.hcsonline.com/api/database-stats

# Reinitialize
curl -X POST https://hcsbot.hcsonline.com/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```

### SSL Certificate
```bash
sudo certbot certificates
sudo certbot renew
```

## 📊 Server Requirements Met

Your LiquidWeb server configuration:
- ✅ **IP**: 67.225.163.130
- ✅ **Domain**: hcsbot.hcsonline.com
- ✅ **RAM**: 4GB+ (8GB recommended)
- ✅ **Storage**: 20GB+
- ✅ **OS**: Ubuntu 22.04 LTS

## 💡 Tips

1. **First Deployment**: May take 15-20 minutes for PDF processing
2. **DNS Propagation**: Can take 5-30 minutes
3. **SSL Setup**: Automatic via Let's Encrypt
4. **Monitoring**: Use `pm2 monit` for real-time metrics

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Check services | `pm2 status` |
| View logs | `pm2 logs` |
| Restart all | `pm2 restart all` |
| Update app | `cd /var/www/hcsbot && git pull && npm run build:liquidweb && pm2 restart all` |
| Test API | `curl https://hcsbot.hcsonline.com/api/health` |
| SSL status | `sudo certbot certificates` |

## 📖 Full Documentation

For detailed information, see:
- **LIQUIDWEB-DEPLOYMENT.md** - Complete deployment guide
- **README.md** - Application overview
- **nginx-liquidweb.conf** - Nginx configuration

## 🎉 Success!

Once deployed, your chatbot will be live at:
- **Frontend**: https://hcsbot.hcsonline.com
- **API**: https://hcsbot.hcsonline.com/api

The chatbot will:
- ✅ Answer questions about Apple technology
- ✅ Provide source citations from PDFs
- ✅ Offer smart suggestions
- ✅ Include admin dashboard

**Cost**: ~$27-50/month (server + API usage)

---

Need help? Check the logs: `pm2 logs`
