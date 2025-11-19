# HCS Apple Technology Assistant - Production Deployment Guide

## Overview
This document outlines the requirements and setup for deploying the HCS Apple Technology Assistant on a production web server.

## System Architecture

The application consists of:
- **Frontend**: React.js application (served as static files)
- **Backend**: FastAPI Python server with RAG system
- **Database**: ChromaDB vector database
- **AI Service**: Claude API (Anthropic) or OpenAI API

## Hardware Requirements

### Minimum Requirements
- **CPU**: 4 cores (Intel/AMD x64 or Apple Silicon)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB SSD minimum
- **Network**: 1Gbps connection

### Recommended Production Setup
- **CPU**: 8+ cores (Intel Xeon, AMD EPYC, or Apple M-series)
- **RAM**: 32GB+ (for optimal vector database performance)
- **Storage**: 
  - 100GB+ NVMe SSD for OS and applications
  - Additional storage for document archives and backups
- **Network**: Multiple Gbps with redundancy

### Cloud Provider Recommendations

#### AWS
- **Instance Type**: t3.xlarge (4 vCPU, 16GB RAM) or c5.2xlarge (8 vCPU, 16GB RAM)
- **Storage**: GP3 SSD with 3,000 IOPS
- **Load Balancer**: Application Load Balancer (ALB)
- **CDN**: CloudFront for static assets

#### Google Cloud Platform
- **Instance Type**: n2-standard-4 (4 vCPU, 16GB RAM) or n2-standard-8 (8 vCPU, 32GB RAM)
- **Storage**: SSD persistent disk
- **Load Balancer**: Google Cloud Load Balancing
- **CDN**: Cloud CDN

#### Azure
- **Instance Type**: Standard_D4s_v3 (4 vCPU, 16GB RAM) or Standard_D8s_v3 (8 vCPU, 32GB RAM)
- **Storage**: Premium SSD
- **Load Balancer**: Azure Load Balancer
- **CDN**: Azure CDN

## Software Requirements

### Operating System
- **Recommended**: Ubuntu 22.04 LTS or Rocky Linux 9
- **Alternative**: Amazon Linux 2, CentOS Stream 9

### Runtime Environment
- **Python**: 3.11+ (3.13 preferred)
- **Node.js**: 18+ (for building React frontend)
- **Nginx**: 1.20+ (reverse proxy and static file serving)
- **SSL**: Let's Encrypt or commercial certificate

## Deployment Architecture

### Production Setup
```
Internet → Load Balancer → Nginx → FastAPI Backend
                      ↘ Static Files (React)
```

### High-Availability Setup
```
Internet → CDN → Load Balancer → Multiple Nginx Instances
                              ↘ Multiple FastAPI Instances
                              ↘ Shared Vector Database
```

## Installation Steps

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git curl

# Install Node.js (for building frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Application Deployment
```bash
# Clone repository (when moved to GitHub)
git clone https://github.com/your-org/hcs-apple-assistant.git
cd hcs-apple-assistant

# Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build React frontend
npm install
npm run build

# Set up environment variables
cp .env.example .env
# Edit .env with production values
```

### 3. Vector Database Setup
```bash
# Initialize vector database with your PDFs
cd backend
python pdf_processor.py --initialize --pdf-path /path/to/your/pdfs/
```

### 4. Nginx Configuration
```nginx
# /etc/nginx/sites-available/hcs-assistant
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Serve React static files
    location / {
        root /var/www/hcs-assistant/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 30s;
    }
}
```

### 5. Systemd Service
```ini
# /etc/systemd/system/hcs-assistant.service
[Unit]
Description=HCS Apple Technology Assistant API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/hcs-assistant/backend
Environment=PATH=/var/www/hcs-assistant/venv/bin
ExecStart=/var/www/hcs-assistant/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## Performance Optimization

### Vector Database Optimization
- **Memory Mapping**: Ensure sufficient RAM for ChromaDB to memory-map indices
- **SSD Storage**: Use high-IOPS SSD for vector database files
- **Batch Processing**: Process document updates in batches during low-traffic periods

### API Optimization
- **Connection Pooling**: Configure Claude/OpenAI API with proper connection pooling
- **Caching**: Implement Redis for frequently asked questions
- **Rate Limiting**: Configure rate limiting to prevent API abuse

### Frontend Optimization
- **CDN**: Serve static assets through CDN
- **Compression**: Enable gzip/brotli compression in Nginx
- **Minification**: Ensure React build is optimized for production

## Security Considerations

### API Keys
- Store all API keys in environment variables
- Use secrets management service (AWS Secrets Manager, Azure Key Vault)
- Rotate keys regularly

### Network Security
- Configure firewall (UFW/iptables) to only allow necessary ports
- Use VPC/private networks in cloud environments
- Implement DDoS protection

### Application Security
- Enable CORS restrictions in FastAPI
- Implement rate limiting
- Use HTTPS everywhere
- Regular security updates

## Monitoring and Logging

### Application Monitoring
- **Logs**: Centralized logging with ELK stack or cloud logging
- **Metrics**: Monitor API response times, error rates, resource usage
- **Health Checks**: Implement comprehensive health check endpoints

### Infrastructure Monitoring
- **Server Resources**: CPU, RAM, disk usage
- **Network**: Bandwidth, latency, packet loss
- **Database**: Query performance, connection counts

## Backup and Disaster Recovery

### Data Backup
```bash
# Vector database backup
tar -czf chromadb-backup-$(date +%Y%m%d).tar.gz /path/to/chroma_db/

# PDF documents backup
rsync -av /path/to/PDFs/ backup-location/PDFs/
```

### Recovery Procedures
- Document database restoration process
- Test recovery procedures regularly
- Maintain offsite backups

## Cost Considerations

### Monthly Estimates (AWS)
- **t3.xlarge instance**: ~$150/month
- **Storage (100GB GP3)**: ~$10/month
- **Data transfer**: ~$20-50/month
- **Load Balancer**: ~$20/month
- **AI API costs**: Variable based on usage

### Cost Optimization
- Use reserved instances for predictable workloads
- Implement auto-scaling for variable traffic
- Monitor and optimize AI API usage
- Use appropriate storage tiers

## Scaling Strategies

### Horizontal Scaling
- Multiple FastAPI instances behind load balancer
- Shared vector database (consider distributed solutions)
- CDN for global distribution

### Vertical Scaling
- Increase instance size as needed
- Monitor resource utilization
- Scale database resources independently

## Maintenance

### Regular Tasks
- **Weekly**: Review logs, performance metrics
- **Monthly**: Security updates, dependency updates
- **Quarterly**: Performance review, cost optimization
- **Annually**: Disaster recovery testing, security audit

### Document Updates
- Automated PDF processing pipeline
- Version control for document changes
- Staging environment for testing updates

## Getting Started

1. Choose your hosting provider and instance size
2. Follow the installation steps above
3. Configure domain and SSL certificates
4. Upload your PDF documents and initialize the vector database
5. Test the system thoroughly before going live
6. Set up monitoring and backup procedures

For additional support with deployment, contact the development team or refer to the technical documentation.