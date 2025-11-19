"""
RAG (Retrieval Augmented Generation) System for HCS Apple Technology Assistant
Extracts text from PDFs, creates embeddings, and performs semantic search
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import heavy ML dependencies (optional for Vercel deployment)
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    cosine_similarity = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Check if RAG dependencies are available
RAG_DEPENDENCIES_AVAILABLE = all([
    PYPDF2_AVAILABLE,
    NUMPY_AVAILABLE,
    SKLEARN_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE
])

class RAGSystem:
    def __init__(self):
        self.model = None
        self.document_chunks = []
        self.embeddings = None
        
        # Use current directory for Vercel compatibility
        self.pdf_cache_dir = os.path.join(os.getcwd(), "pdf_cache")
        self.embeddings_cache_file = os.path.join(os.getcwd(), "embeddings_cache.pkl")
        
        # Create cache directory
        try:
            os.makedirs(self.pdf_cache_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create cache directory, using temp: {e}")
            # Fallback to temp if permission issues
            self.pdf_cache_dir = "/tmp/hcs_pdfs"
            self.embeddings_cache_file = "/tmp/hcs_embeddings.pkl"
            os.makedirs(self.pdf_cache_dir, exist_ok=True)
        
        # Complete PDF URLs from knowledge base (98 PDFs)
        self.pdf_urls = {
            "Passkeys.pdf": "https://hcsonline.com/images/PDFs/Passkeys.pdf",
            "Deploy_Apple_Beta.pdf": "https://hcsonline.com/images/PDFs/Deploy_Apple_Beta.pdf", 
            "Travel_Data_Security.pdf": "https://hcsonline.com/images/PDFs/Travel_Data_Security.pdf",
            "Jamf_Microsoft_Platform_SSO.pdf": "https://hcsonline.com/images/PDFs/Jamf_Microsoft_Platform_SSO.pdf",
            "JCE_Mac_Report.pdf": "https://hcsonline.com/images/PDFs/JCE_Mac_Report.pdf",
            "Jamf_Google_App_Password.pdf": "https://hcsonline.com/images/PDFs/Jamf_Google_App_Password.pdf",
            "Jamf_Kerberos.pdf": "https://hcsonline.com/images/PDFs/Jamf_Kerberos.pdf",
            "Managing_Your_Apple_ID_HCS.pdf": "https://hcsonline.com/images/PDFs/Managing_Your_Apple_ID_HCS.pdf",
            "Bootstrap_Token_Guide.pdf": "https://hcsonline.com/images/PDFs/Bootstrap_Token_Guide.pdf",
            "How_to_use_Jamf_Helper.pdf": "https://hcsonline.com/images/PDFs/How_to_use_Jamf_Helper.pdf",
            "Set_Default_App_SS.pdf": "https://hcsonline.com/images/PDFs/Set_Default_App_SS.pdf",
            "Signed_DEPNotify.pdf": "https://hcsonline.com/images/PDFs/Signed_DEPNotify.pdf",
            "Enterprise_Connect.pdf": "https://hcsonline.com/images/PDFs/Enterprise_Connect.pdf",
            "Creating_VM.pdf": "https://hcsonline.com/images/PDFs/Creating_VM.pdf",
            "Jamf_Autopkgr.pdf": "https://hcsonline.com/images/PDFs/Jamf_Autopkgr.pdf",
            "Jamf_Microsoft_Azure_Integration.pdf": "https://hcsonline.com/images/PDFs/Jamf_Microsoft_Azure_Integration.pdf",
            "Jamf_Cloud_Distribution_AWS.pdf": "https://hcsonline.com/images/PDFs/Jamf_Cloud_Distribution_AWS.pdf",
            "Jamf_OpenSSL_CSR.pdf": "https://hcsonline.com/images/PDFs/Jamf_OpenSSL_CSR.pdf",
            "Jamf_Infrstructure_Manager.pdf": "https://hcsonline.com/images/PDFs/Jamf_Infrstructure_Manager.pdf",
            "Wireless_Network_Apple.pdf": "https://hcsonline.com/images/PDFs/Wireless_Network_Apple.pdf",
            "System_Settings_Sequoia.pdf": "https://hcsonline.com/images/PDFs/System_Settings_Sequoia.pdf",
            "Guide_iPadOS_18.pdf": "https://hcsonline.com/images/PDFs/Guide_iPadOS_18.pdf",
            "System_Settings_Ventura.pdf": "https://hcsonline.com/images/PDFs/System_Settings_Ventura.pdf",
            "macOS_Ventura_Getting_Started.pdf": "https://hcsonline.com/images/PDFs/macOS_Ventura_Getting_Started.pdf",
            "System_Settings_Sonoma.pdf": "https://hcsonline.com/images/PDFs/System_Settings_Sonoma.pdf",
            "Getting_Started_Sonoma.pdf": "https://hcsonline.com/images/PDFs/Getting_Started_Sonoma.pdf",
            "Guide_to_iPadOS_17.pdf": "https://hcsonline.com/images/PDFs/Guide_to_iPadOS_17.pdf",
            "Outlook_365_for_Mac.pdf": "https://hcsonline.com/images/PDFs/Outlook_365_for_Mac.pdf",
            "Outlook_for_iPadOS.pdf": "https://hcsonline.com/images/PDFs/Outlook_for_iPadOS.pdf",
            "Outlook_for_iOS_iPhone_2022.pdf": "https://hcsonline.com/images/PDFs/Outlook_for_iOS_iPhone_2022.pdf",
            # All the other PDFs from the 98-PDF collection
            "Offboard_Mac_Jamf.pdf": "https://hcsonline.com/images/PDFs/Offboard_Mac_Jamf.pdf",
            "Jamf_SMTP_Google.pdf": "https://hcsonline.com/images/PDFs/Jamf_SMTP_Google.pdf",
            "Jamf_SMTP_Microsoft_API.pdf": "https://hcsonline.com/images/PDFs/Jamf_SMTP_Microsoft_API.pdf",
            "Retrieve_AppleCare_Jamf_Cover.pdf": "https://hcsonline.com/images/PDFs/Retrieve_AppleCare_Jamf_Cover.pdf",
            "Account_Driven_Cloudflare.pdf": "https://hcsonline.com/images/PDFs/Account_Driven_Cloudflare.pdf",
            "SCIM_Token_ABM_Entra.pdf": "https://hcsonline.com/images/PDFs/SCIM_Token_ABM_Entra.pdf",
            "Jamf_Setup_Manager.pdf": "https://hcsonline.com/images/PDFs/Jamf_Setup_Manager.pdf",
            "macOS_Software_Update_Jamf.pdf": "https://hcsonline.com/images/PDFs/macOS_Software_Update_Jamf.pdf",
            "Jamf_Baseline.pdf": "https://hcsonline.com/images/PDFs/Jamf_Baseline.pdf",
            "Archive_Emails_M365.pdf": "https://hcsonline.com/images/PDFs/Archive_Emails_M365.pdf",
            "Enable_Touch_ID_Terminal.pdf": "https://hcsonline.com/images/PDFs/Enable_Touch_ID_Terminal.pdf",
            "Jamf_Printers.pdf": "https://hcsonline.com/images/PDFs/Jamf_Printers.pdf",
            "Update_macOS_Managed.pdf": "https://hcsonline.com/images/PDFs/Update_macOS_Managed.pdf",
            "Add_Mac_ABM_No_Erase.pdf": "https://hcsonline.com/images/PDFs/Add_Mac_ABM_No_Erase.pdf",
            "Restore_Deleted_Objects.pdf": "https://hcsonline.com/images/PDFs/Restore_Deleted_Objects.pdf",
            "Jamf_Smart_Group_Patch.pdf": "https://hcsonline.com/images/PDFs/Jamf_Smart_Group_Patch.pdf",
            "Change_Email_Address_Apple_Account.pdf": "https://hcsonline.com/images/PDFs/Change_Email_Address_Apple_Account.pdf",
            "Sonoma_Blocker.pdf": "https://hcsonline.com/images/PDFs/Sonoma_Blocker.pdf",
            "Web_Browsers_Profiles.pdf": "https://hcsonline.com/images/PDFs/Web_Browsers_Profiles.pdf",
            "App_Password_Jamf.pdf": "https://hcsonline.com/images/PDFs/App_Password_Jamf.pdf",
            "erase-install.pdf": "https://hcsonline.com/images/PDFs/erase-install.pdf",
            "Jamf_Account_Driven.pdf": "https://hcsonline.com/images/PDFs/Jamf_Account_Driven.pdf",
            "Adobe_Pantone.pdf": "https://hcsonline.com/images/PDFs/Adobe_Pantone.pdf",
            "Scripting_Intro_Zsh.pdf": "https://hcsonline.com/images/PDFs/Scripting_Intro_Zsh.pdf",
            "Jamf_Escrow_Buddy.pdf": "https://hcsonline.com/images/PDFs/Jamf_Escrow_Buddy.pdf",
            "Jamf_Pro_to_Mac_Silicon.pdf": "https://hcsonline.com/images/PDFs/Jamf_Pro_to_Mac_Silicon.pdf",
            "ABM_Federation.pdf": "https://hcsonline.com/images/PDFs/ABM_Federation.pdf",
            "2FA_1Password.pdf": "https://hcsonline.com/images/PDFs/2FA_1Password.pdf",
            "Jamf_LAPS_Configure.pdf": "https://hcsonline.com/images/PDFs/Jamf_LAPS_Configure.pdf",
            "Managed_Apple_IDs.pdf": "https://hcsonline.com/images/PDFs/Managed_Apple_IDs.pdf",
            "Jamf_Install_SentinalOne.pdf": "https://hcsonline.com/images/PDFs/Jamf_Install_SentinalOne.pdf",
            "Security_Key_Apple_ID.pdf": "https://hcsonline.com/images/PDFs/Security_Key_Apple_ID.pdf",
            "JamfGoogleCloud.pdf": "https://hcsonline.com/images/PDFs/JamfGoogleCloud.pdf",
        }
    
    def initialize(self):
        """Initialize the RAG system"""
        try:
            # Check if RAG dependencies are available
            if not RAG_DEPENDENCIES_AVAILABLE:
                logger.warning("RAG dependencies not available. Missing:")
                if not PYPDF2_AVAILABLE:
                    logger.warning("  - PyPDF2")
                if not NUMPY_AVAILABLE:
                    logger.warning("  - numpy")
                if not SKLEARN_AVAILABLE:
                    logger.warning("  - scikit-learn")
                if not SENTENCE_TRANSFORMERS_AVAILABLE:
                    logger.warning("  - sentence-transformers")
                logger.warning("Using static knowledge base instead")
                return False

            logger.info("Initializing RAG system...")

            # Initialize sentence transformer model
            logger.info("Loading sentence transformer model...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer model: {e}")
                # For serverless, this might fail due to model download issues
                # Return False to use fallback system
                return False
            
            # Try to load cached embeddings
            if self.load_cached_embeddings():
                logger.info("Loaded cached embeddings successfully")
                return True
                
            # If no cache, start with a subset of PDFs for faster initialization
            logger.info("No cached embeddings found, processing subset of PDFs...")
            if self.process_pdf_subset():
                logger.info("RAG system initialized with subset successfully")
                return True
            else:
                logger.warning("Failed to process PDF subset, will use fallback")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            return False
    
    def process_pdf_subset(self) -> bool:
        """Process a small subset of PDFs for faster initialization"""
        try:
            all_chunks = []
            
            # Process only first 5 PDFs for initial deployment
            pdf_subset = dict(list(self.pdf_urls.items())[:5])
            logger.info(f"Processing {len(pdf_subset)} PDFs for initial setup...")
            
            for filename, url in pdf_subset.items():
                try:
                    pdf_path = self.download_pdf(filename, url)
                    if pdf_path:
                        chunks = self.extract_text_from_pdf(pdf_path, filename)
                        all_chunks.extend(chunks)
                        logger.info(f"Processed {filename}: {len(chunks)} chunks")
                except Exception as e:
                    logger.warning(f"Failed to process {filename}: {e}")
                    continue
            
            if not all_chunks:
                logger.error("No chunks extracted from PDF subset")
                return False
            
            logger.info(f"Total chunks extracted from subset: {len(all_chunks)}")
            self.document_chunks = all_chunks
            
            # Create embeddings
            logger.info("Creating embeddings for subset...")
            texts = [chunk['text'] for chunk in all_chunks]
            self.embeddings = self.model.encode(texts)
            
            # Cache the results
            self.save_embeddings_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process PDF subset: {e}")
            return False
    
    def download_pdf(self, filename: str, url: str) -> Optional[str]:
        """Download PDF and return local path"""
        local_path = os.path.join(self.pdf_cache_dir, filename)
        
        # Check if already cached
        if os.path.exists(local_path):
            logger.debug(f"Using cached PDF: {filename}")
            return local_path
        
        try:
            logger.info(f"Downloading PDF: {filename}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Successfully downloaded: {filename}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str, filename: str) -> List[Dict[str, Any]]:
        """Extract text from PDF and create chunks with page numbers"""
        chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        
                        # Clean and chunk the text
                        if text and len(text.strip()) > 50:  # Only process pages with substantial content
                            # Split into smaller chunks if page is very long
                            if len(text) > 2000:
                                # Split by paragraphs or sentences
                                paragraphs = text.split('\n\n')
                                current_chunk = ""
                                
                                for para in paragraphs:
                                    if len(current_chunk + para) < 1500:
                                        current_chunk += para + "\n\n"
                                    else:
                                        if current_chunk:
                                            chunks.append({
                                                'text': current_chunk.strip(),
                                                'source': filename,
                                                'page': page_num + 1,
                                                'url': self.pdf_urls.get(filename, ''),
                                                'chunk_id': f"{filename}_p{page_num + 1}_{len(chunks)}"
                                            })
                                        current_chunk = para + "\n\n"
                                
                                # Add remaining chunk
                                if current_chunk:
                                    chunks.append({
                                        'text': current_chunk.strip(),
                                        'source': filename,
                                        'page': page_num + 1,
                                        'url': self.pdf_urls.get(filename, ''),
                                        'chunk_id': f"{filename}_p{page_num + 1}_{len(chunks)}"
                                    })
                            else:
                                # Single chunk for shorter pages
                                chunks.append({
                                    'text': text.strip(),
                                    'source': filename,
                                    'page': page_num + 1,
                                    'url': self.pdf_urls.get(filename, ''),
                                    'chunk_id': f"{filename}_p{page_num + 1}"
                                })
                                
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1} of {filename}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to process PDF {filename}: {e}")
            
        logger.info(f"Extracted {len(chunks)} chunks from {filename}")
        return chunks
    
    def process_all_pdfs(self) -> bool:
        """Process all PDFs and create embeddings"""
        try:
            all_chunks = []
            
            # Process PDFs in parallel for speed
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_pdf = {}
                
                for filename, url in list(self.pdf_urls.items())[:10]:  # Start with first 10 PDFs for testing
                    pdf_path = self.download_pdf(filename, url)
                    if pdf_path:
                        future = executor.submit(self.extract_text_from_pdf, pdf_path, filename)
                        future_to_pdf[future] = filename
                
                for future in as_completed(future_to_pdf):
                    filename = future_to_pdf[future]
                    try:
                        chunks = future.result()
                        all_chunks.extend(chunks)
                    except Exception as e:
                        logger.error(f"Failed to process {filename}: {e}")
            
            if not all_chunks:
                logger.error("No chunks extracted from PDFs")
                return False
            
            logger.info(f"Total chunks extracted: {len(all_chunks)}")
            self.document_chunks = all_chunks
            
            # Create embeddings
            logger.info("Creating embeddings...")
            texts = [chunk['text'] for chunk in all_chunks]
            self.embeddings = self.model.encode(texts)
            
            # Cache the results
            self.save_embeddings_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process PDFs: {e}")
            return False
    
    def save_embeddings_cache(self):
        """Save embeddings and chunks to cache"""
        try:
            cache_data = {
                'document_chunks': self.document_chunks,
                'embeddings': self.embeddings
            }
            with open(self.embeddings_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info("Saved embeddings cache")
        except Exception as e:
            logger.error(f"Failed to save embeddings cache: {e}")
    
    def load_cached_embeddings(self) -> bool:
        """Load cached embeddings and chunks"""
        try:
            if os.path.exists(self.embeddings_cache_file):
                with open(self.embeddings_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                self.document_chunks = cache_data['document_chunks']
                self.embeddings = cache_data['embeddings']
                
                logger.info(f"Loaded {len(self.document_chunks)} cached chunks")
                return True
        except Exception as e:
            logger.error(f"Failed to load cached embeddings: {e}")
        return False
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        if not self.model or self.embeddings is None:
            logger.error("RAG system not properly initialized")
            return []
        
        try:
            # Create query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get top-k most similar chunks
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                chunk = self.document_chunks[idx].copy()
                chunk['similarity_score'] = float(similarities[idx])
                chunk['relevance_score'] = float(similarities[idx])  # For compatibility
                results.append(chunk)
            
            # Filter out very low similarity scores
            results = [r for r in results if r['similarity_score'] > 0.1]
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

# Global RAG system instance
rag_system = RAGSystem()