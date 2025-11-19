# HCS Apple Technology Chatbot - Docker Deployment

Complete Docker setup for Mac Mini M4 server using GPT-4o Mini API.

## 🚀 Quick Start

### 1. Deploy to Mac Mini M4
```bash
# Copy project to Mac Mini
scp -r . user@192.168.86.100:~/hcs-chatbot

# SSH to Mac Mini
ssh user@192.168.86.100
cd hcs-chatbot

# Deploy with Docker
./deploy-docker.sh
```

### 2. Set up Cloudflare Tunnels (Optional)
```bash
# Set up tunnels for public access
./setup-tunnel.sh
```

## 📋 Configuration

### Mac Mini M4 Server Details:
- **IP Address**: 192.168.86.100
- **API**: GPT-4o Mini (95% cheaper than Claude)
- **Cost**: ~$0.005 per query
- **Architecture**: ARM64 optimized

### Services:
- **Frontend**: http://192.168.86.100:3000
- **Backend API**: http://192.168.86.100:8000  
- **Redis**: 192.168.86.100:6379

## 🛠 Management Commands

```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose build --no-cache && docker-compose up -d
```

## 🔧 Configuration Files

### Key Files:
- **docker-compose.yml**: Main service configuration
- **.env.docker**: Environment variables template
- **Dockerfile.frontend**: React app container
- **backend/Dockerfile**: Python API container
- **nginx.conf**: Frontend server configuration

### Environment Variables:
```bash
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-PdcSkyOgGWLTaBhJcQmWUSbVqGHt3zsoBMjO0qJPJ_T3BlbkFJLkHxPmx2lgkWB010tSEv5vAJWbGJ8_SfaNvHOZWdkA
REACT_APP_API_URL=http://192.168.86.100:8000
```

## 💰 Cost Analysis

### GPT-4o Mini Pricing:
- **Input tokens**: $0.15 per 1M tokens
- **Output tokens**: $0.60 per 1M tokens
- **Per query**: ~$0.005 average
- **Monthly estimate**: $5-20 for typical usage

### Savings vs Alternatives:
- **vs Claude 3.5**: Save 95% (~$50-200/month)
- **vs Local LLM**: Save on hardware/electricity
- **vs Cloud hosting**: Save $25-100/month on servers

## 🌐 Network Access

### Local Network:
All devices on 192.168.86.x can access:
- Frontend: http://192.168.86.100:3000
- API: http://192.168.86.100:8000

### Public Access (via Cloudflare Tunnels):
- Frontend: https://llm.tektest.org
- API: https://hcs-api.tektest.org

## 🔍 Troubleshooting

### Check Service Health:
```bash
# Backend health
curl http://192.168.86.100:8000/health

# Frontend
curl http://192.168.86.100:3000

# View logs
docker-compose logs -f hcs-backend
```

### Common Issues:
1. **Port conflicts**: Stop other services using ports 3000/8000
2. **Permission errors**: Check file permissions and Docker access
3. **API key issues**: Verify OpenAI API key in .env file
4. **Memory issues**: Mac Mini M4 should handle this easily

## 🚀 Production Deployment

### Steps:
1. Deploy containers on Mac Mini
2. Configure Cloudflare tunnels
3. Update DNS records
4. Test mobile/external access

### Monitoring:
- Health checks: Built into containers
- Logs: `docker-compose logs -f`
- Metrics: Container stats with `docker stats`

## 📱 Mobile Testing

The setup is optimized for mobile Safari and Chrome with:
- CORS headers configured
- Mobile-specific middleware
- Responsive design
- Touch-friendly interface

Test on various devices once deployed!