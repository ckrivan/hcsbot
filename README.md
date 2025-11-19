# HCS Apple Technology Chatbot

A RAG-powered chatbot that provides expert guidance on Apple device management, Jamf Pro, iOS deployment, and enterprise Apple solutions based on HCS's comprehensive PDF documentation library.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Claude API Key (recommended) or OpenAI API Key

### 1. Setup Environment
```bash
# Clone or navigate to project directory
cd HCS

# Copy environment template
cp .env.example .env

# Edit .env and add your Claude API key (recommended for better performance)
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# LLM_PROVIDER=claude
# CLAUDE_MODEL=claude-3-5-haiku-20241022  # Cheapest option

# OR if you prefer OpenAI:
# OPENAI_API_KEY=sk-your-key-here
# LLM_PROVIDER=openai
```

### 2. Start the Application
```bash
# Make startup script executable (if needed)
chmod +x start.sh

# Start both backend and frontend
./start.sh
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

### 3. Demo with Cloudflare Tunnel
```bash
# In a separate terminal, after the app is running
./setup_tunnel.sh
```

This will create a public URL for demo purposes.

## 📚 Features

- **Intelligent Q&A**: Ask questions about Apple technology and get accurate answers
- **Source Citations**: Every answer includes PDF source and page references
- **Sample Questions**: Pre-loaded demo questions for easy testing
- **Real-time Chat**: Responsive chat interface with typing indicators
- **PDF Integration**: Processes 80+ Apple technology PDFs automatically

## 🛠 Technical Architecture

### Backend (FastAPI)
- **PDF Processing**: Extracts and chunks text from PDF documents
- **Vector Database**: ChromaDB for semantic search
- **RAG System**: OpenAI GPT-4 integration with context retrieval
- **API Endpoints**: RESTful chat interface

### Frontend (React)
- **Chat Interface**: Modern, responsive design
- **Real-time Updates**: Async communication with backend
- **Source Display**: Shows PDF sources with page numbers
- **Mobile Friendly**: Responsive design for all devices

### Data Pipeline
1. **PDF Extraction**: Text extraction from all PDFs in `/PDFs` folder
2. **Chunking**: Intelligent text segmentation with metadata
3. **Embedding**: Sentence transformer embeddings for semantic search
4. **Indexing**: ChromaDB vector storage for fast retrieval
5. **RAG**: Context-aware response generation

## 📋 Sample Questions

Try asking about:
- "How do I deploy Zoom using Jamf Pro?"
- "What are the requirements for iOS 18 device management?"
- "How do I set up Apple Configurator 2 blueprints?"
- "What is the process for enrolling devices in Apple Business Manager?"
- "How do I configure Microsoft 365 with Jamf Connect?"

## 🔧 API Endpoints

- `GET /` - Health check
- `POST /chat` - Main chat endpoint
- `GET /sample-questions` - Get demo questions
- `GET /health` - System status
- `POST /initialize` - Reinitialize system
- `GET /database-stats` - Vector DB statistics

## 📁 Project Structure

```
HCS/
├── backend/
│   ├── app.py              # FastAPI main application
│   ├── pdf_processor.py    # PDF text extraction
│   ├── vector_db.py        # ChromaDB integration
│   └── rag_system.py       # RAG pipeline with OpenAI
├── src/
│   ├── App.js              # Main React component
│   ├── index.js            # React entry point
│   └── index.css           # Styling
├── PDFs/                   # Apple technology documentation
├── public/
│   └── index.html          # HTML template
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── start.sh               # Startup script
└── setup_tunnel.sh        # Cloudflare tunnel setup
```

## 🔒 Security Notes

- API keys are stored in `.env` file (never commit to git)
- Local ChromaDB storage (no external data transmission)
- Cloudflare tunnels are temporary and secure

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python3 --version`
- Verify OpenAI API key in `.env` file
- Install dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Check Node.js version: `node --version`
- Install dependencies: `npm install`
- Clear npm cache: `npm cache clean --force`

### No responses from chatbot
- Check backend health: http://localhost:8000/health
- Verify PDFs are in `/PDFs` folder
- Check OpenAI API key and quota

### Tunnel setup issues
- Install cloudflared: `brew install cloudflared` (macOS)
- Ensure app is running on localhost:3000
- Check firewall settings

## 📞 Support

For technical support with HCS Apple Technology solutions, contact:
- **Website**: https://hcsonline.com
- **Expertise**: Apple Business Manager, Jamf Pro, iOS/iPadOS deployment

---

*Built with ❤️ for HCS Technology Group*# hcsbot
