# HCS Chatbot: Docker Deployment on Mac Mini M4

## Why Docker on Mac Mini is Perfect

### **Docker Advantages:**
✅ **Consistent environment**: Works identically everywhere  
✅ **Easy updates**: `docker pull` and restart  
✅ **Resource isolation**: Clean separation of services  
✅ **Backup/migration**: Export containers easily  
✅ **Development parity**: Same setup as your dev machine  

## Docker Compose Setup

### **Create docker-compose.yml:**
```yaml
version: '3.8'
services:
  hcs-frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://localhost:8000
    volumes:
      - ./build:/app/build
    restart: unless-stopped

  hcs-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - LLM_PROVIDER=ollama
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./backend:/app
      - ./chroma_db:/app/chroma_db
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped

  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --config /etc/cloudflared/config.yml run hcs-api
    volumes:
      - ./tunnel-config.yml:/etc/cloudflared/config.yml:ro
      - ~/.cloudflared:/etc/cloudflared/creds:ro
    restart: unless-stopped
    depends_on:
      - hcs-backend

volumes:
  ollama_data:
```

### **Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY build/ ./build/
EXPOSE 3000
CMD ["npx", "serve", "-s", "build", "-l", "3000"]
```

### **Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

## Mac Mini Setup Process

### **1. Install Docker Desktop** (5 minutes)
```bash
# Download from docker.com or use Homebrew
brew install --cask docker
# Start Docker Desktop app
```

### **2. Clone and Setup** (10 minutes)
```bash
# Clone your repository
git clone <your-repo> ~/hcs-chatbot
cd ~/hcs-chatbot

# Create the Docker setup
# (Copy docker-compose.yml and Dockerfiles above)
```

### **3. Build and Start** (15 minutes)
```bash
# Build all containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### **4. Setup Local LLM** (10 minutes)
```bash
# Download model (runs inside ollama container)
docker-compose exec ollama ollama pull llama3.2:7b

# Test the model
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:7b", "prompt": "Hello!"}'
```

## Local LLM Integration

### **Update Backend for Ollama:**
```python
# In your backend/app.py
import requests

def query_local_llm(prompt, context=""):
    """Query local Ollama LLM"""
    payload = {
        "model": "llama3.2:7b",
        "prompt": f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:",
        "stream": False
    }
    
    response = requests.post(
        "http://ollama:11434/api/generate",
        json=payload,
        timeout=30
    )
    
    return response.json()["response"]
```

## Performance Optimization

### **Mac Mini M4 Pro Docker Settings:**
```bash
# Allocate resources in Docker Desktop:
# - CPUs: 6-8 (leave 2 for macOS)
# - Memory: 16-20GB (leave 4GB for macOS)
# - Disk: 100GB+
```

### **Ollama Performance Tuning:**
```yaml
# In docker-compose.yml ollama service:
environment:
  - OLLAMA_NUM_PARALLEL=4
  - OLLAMA_MAX_LOADED_MODELS=1
  - OLLAMA_FLASH_ATTENTION=1
deploy:
  resources:
    limits:
      memory: 16G
```

## Management Commands

### **Daily Operations:**
```bash
# Start services
docker-compose up -d

# Stop services  
docker-compose down

# View logs
docker-compose logs -f hcs-backend

# Restart specific service
docker-compose restart hcs-backend

# Update and rebuild
git pull
docker-compose build --no-cache
docker-compose up -d
```

### **Monitoring:**
```bash
# Resource usage
docker stats

# Service status
docker-compose ps

# Health checks
curl http://localhost:8000/health
curl http://localhost:3000
```

## Backup Strategy

### **Container Backup:**
```bash
# Export database
docker-compose exec hcs-backend python backup_db.py

# Backup Docker volumes
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama-backup.tar.gz /data

# Config backup
cp docker-compose.yml tunnel-config.yml ~/backups/
```

## Deployment Benefits

### **Enterprise Advantages:**
✅ **Scalable**: Easy to add more containers/models  
✅ **Maintainable**: Clean separation of concerns  
✅ **Debuggable**: Individual container logs  
✅ **Updatable**: Rolling updates without downtime  
✅ **Portable**: Same setup anywhere  

### **Cost Control at Scale:**
- **5,000 queries/day**: $0 API costs with local LLM
- **10,000+ queries/day**: Still $0 API costs
- **Only costs**: Electricity (~$15/month) + hardware amortization

### **Performance Expectations:**
- **Concurrent users**: 50-100 with proper queuing
- **Response time**: 3-8 seconds (faster than current API calls)
- **Reliability**: Container auto-restart + health checks

## Migration Timeline

### **Phase 1: Docker Setup** (1 hour)
1. Install Docker Desktop on Mac Mini
2. Create Docker configuration files
3. Test locally

### **Phase 2: Local LLM** (30 minutes)
1. Download and test Llama model
2. Update backend to use Ollama
3. Verify quality with sample queries

### **Phase 3: Production Switch** (15 minutes)
1. Start Docker services on Mac Mini
2. Update Cloudflare tunnel configuration
3. Switch DNS/tunnel endpoints

**Total deployment time: ~2 hours**
**Downtime: ~5-10 minutes for DNS switch**

This Docker approach gives you enterprise-grade deployment with the cost benefits of local inference - perfect for HCS's scale and authority in the Apple Enterprise space!