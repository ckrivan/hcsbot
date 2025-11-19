import requests
import json
from typing import List, Dict, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystemOllama:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://ollama:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2:7b')  # Use Llama 3.2 7B for better performance
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using Ollama with retrieved context"""
        try:
            # Format context from retrieved documents
            context_text = self._format_context(context_docs)
            
            # Create the prompt
            system_prompt = """You are an expert Apple technology consultant for HCS Technology Group. 
            You help customers with Apple device management, Jamf Pro, iOS/iPadOS deployment, and enterprise Apple solutions.
            
            Use the provided PDF documentation to answer questions accurately. Always cite your sources with the PDF filename and page number.
            If you can't find the answer in the provided context, say so clearly.
            
            Be concise, professional, and focus on practical solutions."""
            
            user_prompt = f"""Question: {query}

Context from HCS Apple documentation:
{context_text}

Please provide a helpful answer based on the documentation above. Include the PDF source and page number for your answer."""

            # Call Ollama API
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response generated')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                answer = "Sorry, I encountered an error processing your question."
            
            return {
                'answer': answer,
                'sources': self._extract_sources(context_docs),
                'query': query,
                'context_used': len(context_docs)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question. Please ensure Ollama is running and try again.",
                'sources': [],
                'query': query,
                'context_used': 0,
                'error': str(e)
            }
    
    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context text"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"Source {i}: {doc['filename']} (Page {doc['page_number']})\n"
                f"Content: {doc['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _extract_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved documents"""
        sources = []
        seen_sources = set()
        
        for doc in docs:
            source_key = f"{doc['filename']}_page_{doc['page_number']}"
            if source_key not in seen_sources:
                sources.append({
                    'filename': doc['filename'],
                    'page_number': doc['page_number'],
                    'similarity_score': doc.get('similarity_score', 0)
                })
                seen_sources.add(source_key)
        
        return sources
    
    def ask_question(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve relevant docs and generate answer"""
        try:
            logger.info(f"Processing question: {question}")
            
            # Retrieve relevant documents
            relevant_docs = self.vector_db.search_similar(question, n_results=n_results)
            
            if not relevant_docs:
                return {
                    'answer': "I couldn't find relevant information in the Apple documentation to answer your question. Please try rephrasing or ask about a different topic.",
                    'sources': [],
                    'query': question,
                    'context_used': 0
                }
            
            # Generate response
            response = self.generate_response(question, relevant_docs)
            
            logger.info(f"Generated response using {len(relevant_docs)} source documents")
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                'answer': "I encountered an error while processing your question. Please ensure Ollama is running and try again.",
                'sources': [],
                'query': question,
                'context_used': 0,
                'error': str(e)
            }
    
    def get_sample_questions(self) -> List[str]:
        """Return sample questions for demo purposes"""
        return [
            "How do I deploy Zoom using Jamf Pro?",
            "What are the requirements for iOS 18 device management?",
            "How do I set up Apple Configurator 2 blueprints?",
            "What is the process for enrolling devices in Apple Business Manager?",
            "How do I configure Microsoft 365 with Jamf Connect?",
            "What are the steps for setting up Bootstrap Token?",
            "How do I manage Apple TV devices through ABM?",
            "What is the process for macOS Sonoma deployment?"
        ]