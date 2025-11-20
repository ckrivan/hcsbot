from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware

from pdf_processor import PDFProcessor
from vector_db import VectorDatabase
from rag_system import RAGSystem
from rag_system_ollama import RAGSystemOllama
from rag_system_claude import RAGSystemClaude
from web_scraper import HCSWebScraper
from article_manifest import ArticleManifest

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="HCS Technology Group - Corby", version="1.0.0")

# Custom middleware for iOS Safari compatibility
class MobileCompatibilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add headers specifically for mobile Safari and Chrome
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        # iOS Safari specific headers
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

# Add mobile compatibility middleware
app.add_middleware(MobileCompatibilityMiddleware)

# Add CORS middleware - configured for mobile compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (including mobile browsers)
    allow_credentials=False,  # Set to False for mobile compatibility
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Request/Response models
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query: str
    context_used: int

class FeedbackRequest(BaseModel):
    query: str
    response: str
    feedback_type: str  # "incorrect", "irrelevant", "missing_info", "other"
    description: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class ReloadRequest(BaseModel):
    force_reload: bool = True

class InitializeRequest(BaseModel):
    force_reload: bool = False

# Global variables
vector_db = None
rag_system = None
is_initialized = False
feedback_storage = []  # Simple in-memory storage for feedback
FEEDBACK_FILE = "./feedback.json"  # Persistent storage file in working directory

# Web scraping globals
web_scraper = None
article_manifest = None
scraping_in_progress = False
last_scrape_status = {"status": "never_run", "timestamp": None, "articles_scraped": 0}

# Query suggestion mappings - maps broad terms to specific questions
QUERY_SUGGESTIONS = {
    "jamf connect": [
        "How do I configure Jamf Connect with Azure AD?",
        "What are the steps to set up Jamf Connect with Google Workspace?", 
        "How do I troubleshoot Jamf Connect login issues?",
        "How do I configure Jamf Connect with Okta?",
        "What are the requirements for Jamf Connect deployment?"
    ],
    "bootstrap token": [
        "How do I set up Bootstrap Token in Jamf Pro?",
        "How do I verify Bootstrap Token status?",
        "What are the prerequisites for Bootstrap Token?",
        "How do I troubleshoot Bootstrap Token issues?"
    ],
    "filevault": [
        "How do I enforce FileVault encryption on macOS devices?",
        "How do I escrow FileVault keys with Jamf Pro?",
        "How do I set up Escrow Buddy for FileVault?",
        "How do I manage FileVault recovery keys?"
    ],
    "zoom": [
        "How do I deploy Zoom using Jamf Pro?",
        "What are the PPPC requirements for Zoom?",
        "How do I configure Zoom settings with a configuration profile?",
        "How do I troubleshoot Zoom deployment issues?"
    ],
    "apple business manager": [
        "How do I enroll devices in Apple Business Manager?",
        "How do I set up automated device enrollment?",
        "How do I manage Apple TV devices through ABM?",
        "How do I configure SCIM with ABM and Entra ID?"
    ],
    "microsoft 365": [
        "How do I configure Microsoft 365 with Jamf Connect?",
        "How do I set up Outlook for macOS?",
        "How do I configure Office 365 authentication?",
        "How do I manage Microsoft 365 licenses?"
    ],
    "abm": [
        "How do I enroll devices in Apple Business Manager?",
        "How do I set up automated device enrollment?", 
        "How do I manage Apple TV devices through ABM?",
        "How do I configure SCIM with ABM and Entra ID?"
    ],
    "escrow buddy": [
        "How do I set up Escrow Buddy for FileVault?",
        "How do I configure Escrow Buddy with Jamf Pro?",
        "How do I troubleshoot Escrow Buddy issues?"
    ]
}

def get_query_suggestions(query: str) -> list:
    """Get intelligent suggestions based on query"""
    query_lower = query.lower().strip()
    
    # Check for exact matches or partial matches
    for key, suggestions in QUERY_SUGGESTIONS.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            return suggestions
    
    return []

def should_suggest_questions(query: str) -> bool:
    """Determine if we should show suggestions instead of a direct answer"""
    query_lower = query.lower().strip()
    
    # If query is very short (3 words or less) and matches our suggestion keys
    if len(query_lower.split()) <= 3:
        for key in QUERY_SUGGESTIONS.keys():
            if key in query_lower or query_lower in key:
                return True
    
    return False

def load_feedback_from_file():
    """Load feedback from persistent file storage"""
    global feedback_storage
    try:
        import json
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                feedback_storage = json.load(f)
            logger.info(f"Loaded {len(feedback_storage)} feedback entries from file")
    except Exception as e:
        logger.error(f"Error loading feedback file: {e}")
        feedback_storage = []

def save_feedback_to_file():
    """Save feedback to persistent file storage"""
    try:
        import json
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(feedback_storage, f, indent=2)
        logger.info(f"Saved {len(feedback_storage)} feedback entries to file")
    except Exception as e:
        logger.error(f"Error saving feedback file: {e}")

def initialize_system(force_reload: bool = False):
    """Initialize or reload the RAG system"""
    global vector_db, rag_system, is_initialized
    
    try:
        logger.info("Initializing RAG system...")
        
        # Initialize vector database
        db_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        vector_db = VectorDatabase(db_path)
        
        # Check if we need to process PDFs
        collection_stats = vector_db.get_collection_stats()
        
        if force_reload or collection_stats.get('total_documents', 0) == 0:
            logger.info("Processing PDF documents...")
            
            # Initialize PDF processor
            pdf_folder = os.getenv('PDF_FOLDER_PATH', '/app/pdfs')
            pdf_processor = PDFProcessor(pdf_folder)
            
            # Process all PDFs
            documents = pdf_processor.process_all_pdfs()
            
            if not documents:
                raise Exception("No PDF documents found or processed")
            
            # Create chunks
            chunks = pdf_processor.create_document_chunks(documents)
            
            # Clear and reload if force_reload
            if force_reload:
                vector_db.clear_collection()
            
            # Add to vector database
            vector_db.add_documents(chunks)
            
            logger.info(f"Processed {len(documents)} PDFs into {len(chunks)} searchable chunks")
        else:
            logger.info(f"Using existing vector database with {collection_stats['total_documents']} documents")
        
        # Initialize RAG system (choose based on environment)
        llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
        
        if use_ollama:
            rag_system = RAGSystemOllama(vector_db)
            logger.info("Using Ollama for local LLM inference")
        elif llm_provider == 'claude':
            rag_system = RAGSystemClaude(vector_db)
            model = os.getenv('CLAUDE_MODEL', 'claude-3-5-haiku-20241022')
            logger.info(f"Using Claude ({model}) for LLM inference")
        else:
            rag_system = RAGSystem(vector_db)
            logger.info("Using OpenAI for LLM inference")
        is_initialized = True
        
        logger.info("RAG system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        is_initialized = False
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    load_feedback_from_file()
    initialize_system()

@app.get("/")
async def root():
    return {"message": "HCS Technology Group - Corby API", "status": "running"}

@app.get("/health")
async def health_check():
    # Test vector database connection
    vector_db_healthy = False
    vector_db_error = None
    
    if vector_db:
        try:
            # Test a simple search to validate everything is working
            test_results = vector_db.search_similar("test", n_results=1)
            vector_db_healthy = True
        except Exception as e:
            vector_db_error = str(e)
            logger.warning(f"Vector database health check failed: {e}")
    
    overall_status = "healthy" if (is_initialized and vector_db_healthy) else "unhealthy"
    
    health_info = {
        "status": overall_status,
        "initialized": is_initialized,
        "vector_db_healthy": vector_db_healthy,
        "database_stats": vector_db.get_collection_stats() if vector_db else {}
    }
    
    if vector_db_error:
        health_info["vector_db_error"] = vector_db_error
    
    return health_info

@app.post("/initialize")
async def initialize_endpoint(request: InitializeRequest):
    """Initialize or reload the system"""
    success = initialize_system(force_reload=request.force_reload)
    
    if success:
        return {
            "message": "System initialized successfully",
            "database_stats": vector_db.get_collection_stats() if vector_db else {}
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize system")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with intelligent suggestions"""
    if not is_initialized or not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized. Please wait or call /initialize")
    
    try:
        # Check if we should provide suggestions instead of direct answer
        suggestions = get_query_suggestions(request.question)
        if suggestions and should_suggest_questions(request.question):
            # Return suggestions instead of generating a response
            suggestion_text = f"## I found several topics related to **{request.question.title()}**\n\n"
            suggestion_text += "Here are some specific questions I can help you with:\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                suggestion_text += f"**{i}.** {suggestion}\n\n"
            suggestion_text += "💡 **Tip:** Click on any of these questions above, or ask me something more specific!"
            
            return ChatResponse(
                answer=suggestion_text,
                sources=[],
                query=request.question,
                context_used=0
            )
        
        # Generate normal response using RAG system
        response = rag_system.ask_question(request.question)
        
        return ChatResponse(
            answer=response['answer'],
            sources=response['sources'],
            query=response['query'],
            context_used=response['context_used']
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Error processing your question")

@app.get("/sample-questions")
async def get_sample_questions():
    """Get sample questions for demo"""
    if not is_initialized or not rag_system:
        return {"questions": []}
    
    return {"questions": rag_system.get_sample_questions()}

@app.get("/database-stats")
async def get_database_stats():
    """Get vector database statistics"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return vector_db.get_collection_stats()

@app.get("/search")
async def search_documents(query: str, limit: int = 5):
    """Search documents directly (for debugging)"""
    if not is_initialized or not vector_db:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        results = vector_db.search_similar(query, n_results=limit)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Error searching documents")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for search results"""
    try:
        # Store feedback in memory with timestamp
        from datetime import datetime
        feedback_entry = {
            "id": len(feedback_storage) + 1,
            "query": request.query,
            "response": request.response[:500],  # Limit response length in logs
            "feedback_type": request.feedback_type,
            "description": request.description,
            "timestamp": datetime.now().isoformat()
        }
        
        feedback_storage.append(feedback_entry)
        save_feedback_to_file()  # Save to persistent storage
        logger.info(f"User feedback received: {feedback_entry}")
        
        return {
            "message": "Thank you for your feedback! We'll use this to improve our responses.",
            "feedback_id": f"fb_{feedback_entry['id']}"
        }
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail="Error processing feedback")

@app.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    # Read credentials from environment variables
    admin_username = os.getenv('ADMIN_USERNAME', 'hcs')
    admin_password = os.getenv('ADMIN_PASSWORD', 'default-password')

    if request.username == admin_username and request.password == admin_password:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/admin/feedback")
async def get_feedback(username: str = None, password: str = None):
    """Get all feedback entries (admin only)"""
    # Read credentials from environment variables
    admin_username = os.getenv('ADMIN_USERNAME', 'hcs')
    admin_password = os.getenv('ADMIN_PASSWORD', 'default-password')

    # Simple auth check via query params (in production, use proper JWT/sessions)
    if username != admin_username or password != admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "total_feedback": len(feedback_storage),
        "feedback": sorted(feedback_storage, key=lambda x: x['timestamp'], reverse=True)
    }

@app.post("/reload")
async def reload_system(request: ReloadRequest):
    """Reload the RAG system and reprocess all PDFs"""
    try:
        logger.info("Reloading system and reprocessing PDFs...")
        success = initialize_system(force_reload=request.force_reload)
        if success:
            return {"message": "System reloaded successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload system")
    except Exception as e:
        logger.error(f"Error reloading system: {e}")
        raise HTTPException(status_code=500, detail=f"Error reloading system: {str(e)}")

@app.get("/pdf/{filename}")
async def get_pdf(filename: str):
    """Serve PDF files with inline viewing support"""
    pdf_folder = os.getenv('PDF_FOLDER_PATH', '/app/pdfs')
    pdf_path = os.path.join(pdf_folder, filename)
    
    
    # Security check - ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=filename,
        headers={
            "Content-Disposition": "inline; filename=" + filename,
            "Cache-Control": "public, max-age=3600"
        }
    )

# Web Scraping Endpoints

@app.post("/scrape/trigger")
async def trigger_scraping():
    """Manually trigger web article scraping from hcsonline.com"""
    global web_scraper, article_manifest, scraping_in_progress, last_scrape_status

    if scraping_in_progress:
        return {"status": "already_running", "message": "Scraping is already in progress"}

    try:
        scraping_in_progress = True
        logger.info("Starting manual web scraping...")

        # Initialize scraper and manifest if needed
        if not web_scraper:
            web_scraper = HCSWebScraper()
        if not article_manifest:
            article_manifest = ArticleManifest()

        # Scrape all articles (2024+ only)
        articles = web_scraper.scrape_all()

        # Update manifest and last scrape status
        last_scrape_status = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "articles_scraped": len(articles),
            "articles_filtered": len([a for a in articles if a]),  # Count non-None articles
        }

        # Store articles in manifest
        for article in articles:
            if article:
                article_manifest.add_article(article)

        scraping_in_progress = False

        return {
            "status": "success",
            "message": f"Scraped {len(articles)} articles from 2024+",
            "articles": [{"title": a["title"], "date": a["published_date"], "url": a["url"]} for a in articles if a]
        }

    except Exception as e:
        scraping_in_progress = False
        last_scrape_status = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        logger.error(f"Error during web scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/scrape/status")
async def get_scraping_status():
    """Get status of web scraping"""
    global article_manifest, scraping_in_progress, last_scrape_status

    if not article_manifest:
        article_manifest = ArticleManifest()

    stats = article_manifest.get_stats()

    return {
        "scraping_in_progress": scraping_in_progress,
        "last_scrape": last_scrape_status,
        "manifest_stats": stats
    }

@app.post("/scrape/add-to-database")
async def add_scraped_articles_to_database():
    """Add scraped articles to vector database"""
    global vector_db, article_manifest

    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector database not initialized")

    if not article_manifest:
        article_manifest = ArticleManifest()

    try:
        logger.info("Adding scraped articles to vector database...")

        # Get all articles from manifest
        articles_data = article_manifest.get_all_articles()

        if not articles_data:
            return {"status": "no_articles", "message": "No articles in manifest to add"}

        # Process articles through PDFProcessor
        pdf_processor = PDFProcessor()
        all_chunks = []
        articles_processed = 0

        for article_entry in articles_data:
            # Skip articles already added to database
            if article_entry.get('chunk_ids'):
                logger.info(f"Skipping already processed article: {article_entry['title']}")
                continue

            # Check if content is stored
            if not article_entry.get('content'):
                logger.warning(f"Skipping article (no content stored): {article_entry['title']}")
                continue

            # Create article data dict for processing
            article_data = {
                'url': article_entry['url'],
                'title': article_entry['title'],
                'content': article_entry['content'],
                'published_date': article_entry.get('published_date'),
                'section': article_entry.get('section', 'blog')
            }

            # Process article into chunks
            chunks = pdf_processor.process_web_article(article_data)

            if chunks:
                all_chunks.extend(chunks)
                articles_processed += 1

                # Update manifest with chunk IDs
                chunk_ids = [chunk['chunk_id'] for chunk in chunks]
                article_manifest.add_article(article_data, chunk_ids=chunk_ids, store_content=True)

                logger.info(f"Processed article: {article_entry['title']} ({len(chunks)} chunks)")

        # Add chunks to vector database
        if all_chunks:
            # Chunks are already in the correct format for add_documents()
            vector_db.add_documents(all_chunks)
            logger.info(f"Added {len(all_chunks)} chunks to vector database")

            return {
                "status": "success",
                "message": f"Processed {articles_processed} articles into vector database",
                "articles_processed": articles_processed,
                "chunks_added": len(all_chunks)
            }
        else:
            return {
                "status": "no_new_articles",
                "message": "No new articles to process (all already in database)"
            }

    except Exception as e:
        logger.error(f"Error adding articles to database: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to add articles: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Check API keys based on provider
    llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
    use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
    
    if use_ollama:
        logger.info("Using Ollama - no API key required")
    elif llm_provider == 'claude':
        if not os.getenv('ANTHROPIC_API_KEY'):
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
            print("Please set your ANTHROPIC_API_KEY in a .env file")
    else:
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY not found in environment variables")
            print("Please set your OPENAI_API_KEY in a .env file")
    
    logger.info("Starting HCS Technology Group - Corby API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")