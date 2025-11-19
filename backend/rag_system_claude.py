import anthropic
from typing import List, Dict, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystemClaude:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-5-haiku-20241022')  # Default to cheapest
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using Claude with retrieved context"""
        try:
            # Format context from retrieved documents
            context_text = self._format_context(context_docs)
            
            # Create the system prompt
            system_prompt = """You are an expert Apple technology consultant for HCS Technology Group. 
You help customers with Apple device management, Jamf Pro, iOS/iPadOS deployment, and enterprise Apple solutions.

IMPORTANT INSTRUCTIONS:
- Use ONLY the provided PDF documentation to answer questions
- Always cite your sources with the exact PDF filename and page number
- If the answer isn't in the provided context, clearly state that you don't have that information
- Be concise, professional, and focus on practical solutions
- Format your response clearly with proper citations

Your expertise areas include:
- Apple Business Manager (ABM)
- Jamf Pro device management
- iOS/iPadOS deployment and configuration
- macOS management and deployment
- Enterprise Apple integrations (Microsoft 365, Azure, etc.)
- Apple Configurator and mobile device management"""

            user_prompt = f"""Question: {query}

Context from HCS Apple documentation:
{context_text}

Please provide a helpful, well-formatted answer based ONLY on the documentation above. 

Format your response as follows:
1. Start with a clear, direct answer
2. Break down the process into numbered steps if applicable
3. Use bullet points for lists or requirements
4. Include specific details like file names, commands, or settings
5. Do NOT include source references in your response text - the system will add them automatically

Focus on providing clear, actionable information based on the documentation."""

            # Call Claude API
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            answer = response.content[0].text
            
            return {
                'answer': answer,
                'sources': self._extract_sources(context_docs),
                'query': query,
                'context_used': len(context_docs),
                'model_used': self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating response with Claude: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question. Please check your Claude API key and try again.",
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
    
    def ask_question(self, question: str, n_results: int = 5, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve relevant docs and generate answer"""
        try:
            logger.info(f"Processing question with Claude: {question}")
            
            # Check if this is a numbered response to a previous clarification
            if self._is_numbered_response(question):
                return self._handle_numbered_response(question, context)
            
            # Retrieve relevant documents
            relevant_docs = self.vector_db.search_similar(question, n_results=n_results)
            
            # Filter out documents with low similarity scores
            min_similarity_threshold = 0.15  # Adjust based on testing
            filtered_docs = [doc for doc in relevant_docs if doc.get('similarity_score', 0) > min_similarity_threshold]
            
            if not filtered_docs:
                return {
                    'answer': "I couldn't find relevant information in the HCS Apple documentation to answer your question. Please try rephrasing your question or ask about topics covered in our Apple technology guides (Jamf Pro, iOS deployment, device management, etc.).\n\n**Tip:** If you think this should have found results, please use the feedback button to report this issue.",
                    'sources': [],
                    'query': question,
                    'context_used': 0,
                    'no_relevant_docs': True
                }
            
            # Check if this might be an ambiguous query that needs clarification
            clarification_response = self._check_for_clarification(question, filtered_docs)
            if clarification_response:
                return clarification_response
            
            # Generate response
            response = self.generate_response(question, filtered_docs)
            
            logger.info(f"Generated response using {len(relevant_docs)} source documents")
            return response
            
        except Exception as e:
            logger.error(f"Error in Claude RAG pipeline: {e}")
            return {
                'answer': "I encountered an error while processing your question. Please ensure your Claude API key is configured correctly and try again.",
                'sources': [],
                'query': question,
                'context_used': 0,
                'error': str(e)
            }
    
    def _check_for_clarification(self, question: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if the query is ambiguous and needs clarification"""
        try:
            # Define ambiguous terms that might need clarification
            ambiguous_terms = {
                'push certificate': ['APNs certificate', 'MDM push certificate', 'push notification certificate'],
                'certificate': ['SSL certificate', 'APNs certificate', 'device certificate', 'identity certificate'],
                'profile': ['configuration profile', 'provisioning profile', 'enrollment profile'],
                'deploy': ['app deployment', 'device deployment', 'configuration deployment'],
                'setup': ['initial setup', 'enrollment setup', 'server setup'],
                'install': ['app installation', 'OS installation', 'certificate installation'],
                'configure': ['device configuration', 'server configuration', 'network configuration']
            }
            
            question_lower = question.lower()
            
            # Check for ambiguous terms
            for term, options in ambiguous_terms.items():
                if term in question_lower:
                    # Check if the similarity scores are low (indicating uncertainty)
                    max_similarity = max([doc.get('similarity_score', 0) for doc in relevant_docs])
                    
                    if max_similarity < 0.2:  # Low confidence threshold
                        numbered_options = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
                        return {
                            'answer': f"I found several possible interpretations for '{term}'. Could you be more specific?\n\n{numbered_options}\n\nPlease respond with the number of your choice (e.g., '1') or rephrase your question with more context.",
                            'sources': [],
                            'query': question,
                            'context_used': 0,
                            'needs_clarification': True,
                            'clarification_options': options,
                            'original_query': question
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in clarification check: {e}")
            return None
    
    def _is_numbered_response(self, question: str) -> bool:
        """Check if the question is just a number (1-9)"""
        return question.strip().isdigit() and 1 <= int(question.strip()) <= 9
    
    def _handle_numbered_response(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle numbered responses to clarification questions"""
        try:
            choice_num = int(question.strip()) - 1  # Convert to 0-based index
            
            # For now, we'll handle this by creating a more specific query
            # In a full implementation, you'd want to track the last clarification context
            ambiguous_terms = {
                'push certificate': ['APNs certificate', 'MDM push certificate', 'push notification certificate'],
                'certificate': ['SSL certificate', 'APNs certificate', 'device certificate', 'identity certificate'],
                'profile': ['configuration profile', 'provisioning profile', 'enrollment profile'],
                'deploy': ['app deployment', 'device deployment', 'configuration deployment'],
                'setup': ['initial setup', 'enrollment setup', 'server setup'],
                'install': ['app installation', 'OS installation', 'certificate installation'],
                'configure': ['device configuration', 'server configuration', 'network configuration']
            }
            
            # For demonstration, let's assume it's about push certificates (most common)
            # In production, you'd store the context from the previous clarification
            options = ambiguous_terms.get('push certificate', [])
            
            if 0 <= choice_num < len(options):
                selected_option = options[choice_num]
                new_query = f"How to create {selected_option}"
                
                # Search with the more specific query
                relevant_docs = self.vector_db.search_similar(new_query, n_results=5)
                
                if relevant_docs:
                    response = self.generate_response(new_query, relevant_docs)
                    logger.info(f"Processed numbered response: {question} -> {selected_option}")
                    return response
                else:
                    return {
                        'answer': f"I found your selection ({selected_option}), but couldn't locate specific documentation for that topic. Please try asking a more detailed question.",
                        'sources': [],
                        'query': new_query,
                        'context_used': 0
                    }
            else:
                return {
                    'answer': f"Please select a valid option number (1-{len(options)}).",
                    'sources': [],
                    'query': question,
                    'context_used': 0
                }
                
        except Exception as e:
            logger.error(f"Error handling numbered response: {e}")
            return {
                'answer': "I had trouble processing your selection. Please try asking your question again with more specific details.",
                'sources': [],
                'query': question,
                'context_used': 0
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
            "What is the process for macOS Sonoma deployment?",
            "How do I set up Azure integration with Jamf?",
            "What are the best practices for iOS app deployment?"
        ]