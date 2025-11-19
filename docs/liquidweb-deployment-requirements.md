# LiquidWeb Deployment Requirements for HCS Apple Technology Assistant

## Server Specifications

### Minimum Requirements:
- **CPU**: 2 vCores
- **RAM**: 4GB (8GB recommended)
- **Storage**: 20GB SSD
- **OS**: Ubuntu 22.04 LTS or CentOS 8

### Recommended Configuration:
- **CPU**: 4 vCores  
- **RAM**: 8GB
- **Storage**: 40GB SSD
- **OS**: Ubuntu 22.04 LTS

## LiquidWeb Product Options

### 1. **VPS Hosting** (Most Cost-Effective)
- **Storm VPS**: Starting ~$15/month
- **CPU**: 2-4 vCores
- **RAM**: 4-8GB
- **Storage**: 40GB SSD
- **Bandwidth**: Unmetered

### 2. **Cloud Dedicated** (High Performance)
- **Intel Xeon**: Starting ~$79/month
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Storage**: 240GB+ SSD
- **Better for high traffic

### 3. **Managed WordPress** (If you want managed)
- **WP Engine alternative**: ~$19/month
- But you'd need custom deployment

## Software Requirements

### System Dependencies:
```bash
# Node.js (18.x or higher)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.9+ 
sudo apt-get install python3 python3-pip python3-venv

# PM2 (Process Manager)
sudo npm install -g pm2

# Nginx (Web Server/Proxy)
sudo apt-get install nginx

# Certbot (SSL Certificates)
sudo apt-get install certbot python3-certbot-nginx
```

## Deployment Architecture

### Without Cloudflare Tunnels:
```
Internet → LiquidWeb Server → Nginx → Your Apps
         ↓
    [Frontend: Port 3000]
    [Backend: Port 8000]
```

### With Nginx Reverse Proxy:
- **Frontend**: `https://llm.tektest.org` → `localhost:3000`
- **Backend**: `https://api.tektest.org` → `localhost:8000`

## Storage Needs

### Database Files:
- **ChromaDB**: ~2-5GB (your vector database)
- **PDF Files**: ~500MB-1GB (Apple documentation)
- **Application**: ~100MB
- **Node modules**: ~500MB

### **Total**: ~4-7GB for application data

## Network/Security Setup

### Firewall Rules:
```bash
# Allow SSH
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

### SSL Certificate:
```bash
# Free Let's Encrypt SSL
sudo certbot --nginx -d llm.tektest.org -d api.tektest.org
```

## Estimated Monthly Costs

### LiquidWeb VPS Option:
- **Storm VPS** (4 vCore, 8GB RAM): ~$25/month
- **SSL Certificate**: Free (Let's Encrypt)
- **Domain**: ~$12/year
- **Total**: ~$26/month

### API Cost Comparison:

#### **Claude 3.5 Sonnet** (Current):
- **Input tokens**: $3.00 per 1M tokens
- **Output tokens**: $15.00 per 1M tokens
- **Quality**: Excellent for complex reasoning
- **Context**: 200K tokens

#### **GPT-4o Mini** (Alternative):
- **Input tokens**: $0.15 per 1M tokens
- **Output tokens**: $0.60 per 1M tokens
- **Quality**: Good for most tasks
- **Context**: 128K tokens

#### Usage Cost Comparison:
| Usage Level | Claude 3.5 Sonnet | GPT-4o Mini | **Savings** |
|-------------|-------------------|-------------|-------------|
| **Light** (100/day) | $10-20/month | $0.50-1/month | **95% less** |
| **Moderate** (500/day) | $50-100/month | $2.50-5/month | **95% less** |
| **Heavy** (2000/day) | $200-400/month | $10-20/month | **95% less** |

#### Per Query Comparison:
| Query Type | Claude 3.5 Sonnet | GPT-4o Mini | **Savings** |
|------------|-------------------|-------------|-------------|
| **Simple** | $0.01-0.03 | $0.0005-0.0015 | **95% less** |
| **Complex** | $0.05-0.15 | $0.0025-0.0075 | **95% less** |
| **With context** | $0.10-0.30 | $0.005-0.015 | **95% less** |

### Total Monthly Costs:

#### **With Claude 3.5 Sonnet:**
- **Server**: ~$25/month
- **API (moderate usage)**: ~$75/month
- **Total**: ~$100/month

#### **With GPT-4o Mini:**
- **Server**: ~$25/month
- **API (moderate usage)**: ~$4/month
- **Total**: ~$29/month

### **Cost Savings: ~$70/month (70% reduction)**

## Local LLM Option Analysis

### Could the VPS run a local LLM?

#### **Storm VPS Specs**: 4 vCore, 8GB RAM, 40GB SSD

#### **Small LLM Requirements**:
- **7B models** (like Llama-3.2-7B): Need ~14GB RAM minimum
- **3B models** (like Llama-3.2-3B): Need ~6GB RAM minimum  
- **1B models** (like Llama-3.2-1B): Need ~2-4GB RAM

### **Verdict: Borderline for tiny models only**

#### **What MIGHT work**:
- **Llama-3.2-1B**: Very basic performance
- **Phi-3 Mini**: Limited reasoning ability
- **TinyLlama**: Poor quality for technical questions

#### **Performance Reality Check**:
- ❌ **CPU inference**: Very slow on VPS (30+ seconds per response)
- ❌ **Quality**: Much worse than GPT-4o Mini for technical questions
- ❌ **Reliability**: Models might crash under load
- ❌ **Memory pressure**: Would impact your web apps

### **Local LLM Monthly Costs**:
- **Server upgrade needed**: 32GB RAM VPS = ~$150/month
- **GPU server**: ~$400-800/month
- **Total**: $150-800/month

### **Recommendation: Stick with APIs**

#### **Why APIs are better**:
✅ **Cost**: GPT-4o Mini at $29/month vs $150+ for local  
✅ **Quality**: Much better performance than small local models  
✅ **Reliability**: 99.9% uptime vs managing your own inference  
✅ **Maintenance**: Zero model updates or optimization needed  
✅ **Scalability**: Handles traffic spikes automatically  

#### **When local LLMs make sense**:
- High-volume applications (10,000+ queries/day)
- Strict data privacy requirements
- Custom fine-tuned models
- Unlimited budget for GPU servers

### **Final Cost Comparison**:
| Option | Monthly Cost | Quality | Maintenance |
|--------|--------------|---------|-------------|
| **GPT-4o Mini API** | $29 | Excellent ⭐⭐⭐⭐⭐ | None |
| **Claude 3.5 API** | $100 | Premium ⭐⭐⭐⭐⭐ | None |
| **Local 1B model** | $150+ | Poor ⭐⭐ | High |
| **Local 7B model** | $400+ | Good ⭐⭐⭐ | High |

### Additional Costs:
- **Domain renewal**: ~$12/year
- **Monitoring tools**: ~$5-10/month (optional)

## Deployment Process

### 1. **Server Setup**:
```bash
# Clone repository
git clone <your-repo>
cd hcs-apple-chatbot

# Install dependencies
npm install
pip install -r requirements.txt

# Build production frontend
npm run build

# Set up PM2 processes
pm2 start backend/app.py --name hcs-backend
pm2 serve build/ 3000 --name hcs-frontend
pm2 save
pm2 startup
```

### 2. **Nginx Configuration**:
```nginx
# /etc/nginx/sites-available/hcs-chatbot
server {
    server_name llm.tektest.org;
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    server_name api.tektest.org;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Pros vs Cloudflare Tunnels

### **LiquidWeb Pros**:
- ✅ More control over server
- ✅ Better for high traffic
- ✅ Traditional hosting approach
- ✅ Can run multiple services

### **LiquidWeb Cons**:
- ❌ More server management required
- ❌ Need to handle SSL certificates
- ❌ More security responsibilities
- ❌ Higher monthly cost (~$25 vs current tunnel costs)

### **Current Tunnel Pros**:
- ✅ Zero server management
- ✅ Automatic SSL/security
- ✅ Global CDN included
- ✅ Lower cost for low traffic

## Recommendation

**Stick with Cloudflare Tunnels** for now because:
1. **Simpler management** - no server maintenance
2. **Lower cost** - especially for current traffic levels  
3. **Better performance** - global CDN included
4. **Automatic security** - SSL, DDoS protection, etc.

**Consider LiquidWeb when:**
- Traffic exceeds tunnel performance
- You need additional server services
- You want more control over the infrastructure