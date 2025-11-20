import os
import PyPDF2
import pdfplumber
from typing import List, Dict, Any
import logging
from pdf_manifest import ExternalPDFManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, pdf_folder_path: str = None):
        self.pdf_folder_path = pdf_folder_path
        self.external_manager = ExternalPDFManager()
        self.use_external = not pdf_folder_path or not os.path.exists(pdf_folder_path)
        
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from a single PDF file"""
        try:
            text_content = []
            filename = os.path.basename(pdf_path)
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append({
                                'page_number': page_num,
                                'text': text.strip(),
                                'filename': filename
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num} from {filename}: {e}")
                        continue
            
            return {
                'filename': filename,
                'pages': text_content,
                'total_pages': len(text_content)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def process_all_pdfs(self) -> List[Dict[str, Any]]:
        """Process all PDFs from local folder or external sources"""
        all_documents = []
        
        if self.use_external:
            logger.info("Using external PDF sources")
            pdf_paths = self.external_manager.get_all_pdf_paths()
            
            for filename, pdf_path in pdf_paths.items():
                logger.info(f"Processing external PDF: {filename}")
                document = self.extract_text_from_pdf(pdf_path)
                if document:
                    all_documents.append(document)
        else:
            # Original local processing logic
            if not os.path.exists(self.pdf_folder_path):
                logger.error(f"PDF folder not found: {self.pdf_folder_path}")
                return all_documents
                
            pdf_files = [f for f in os.listdir(self.pdf_folder_path) if f.lower().endswith('.pdf')]
            logger.info(f"Found {len(pdf_files)} PDF files to process")
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(self.pdf_folder_path, pdf_file)
                logger.info(f"Processing: {pdf_file}")
                
                document = self.extract_text_from_pdf(pdf_path)
                if document:
                    all_documents.append(document)
                
        logger.info(f"Successfully processed {len(all_documents)} PDF files")
        return all_documents
    
    def chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks with better structure preservation"""
        # Clean up the text first
        text = self._clean_text(text)
        
        # Split by paragraphs first, then by sentences if needed
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # If paragraph is small enough, add to current chunk
            if len(current_chunk.split()) + len(paragraph.split()) <= chunk_size:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If paragraph is too big, split it
                if len(paragraph.split()) > chunk_size:
                    words = paragraph.split()
                    for i in range(0, len(words), chunk_size - overlap):
                        chunk = ' '.join(words[i:i + chunk_size])
                        if chunk.strip():
                            chunks.append(chunk.strip())
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and structure text from PDFs"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Add paragraph breaks for common patterns
        text = text.replace('. Step ', '.\n\nStep ')
        text = text.replace('. Note:', '.\n\nNote:')
        text = text.replace('. Important:', '.\n\nImportant:')
        text = text.replace('. Warning:', '.\n\nWarning:')
        text = text.replace('1. ', '\n\n1. ')
        text = text.replace('2. ', '\n\n2. ')
        text = text.replace('3. ', '\n\n3. ')
        text = text.replace('4. ', '\n\n4. ')
        text = text.replace('5. ', '\n\n5. ')
        
        # Clean up multiple newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
            
        return text
    
    def create_document_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create searchable chunks from all documents"""
        all_chunks = []
        
        for doc in documents:
            filename = doc['filename']
            
            for page_data in doc['pages']:
                page_num = page_data['page_number']
                text = page_data['text']
                
                chunks = self.chunk_text(text)
                
                for chunk_idx, chunk in enumerate(chunks):
                    all_chunks.append({
                        'text': chunk,
                        'filename': filename,
                        'page_number': page_num,
                        'chunk_id': f"{filename}_page{page_num}_chunk{chunk_idx}",
                        'metadata': {
                            'source': filename,
                            'source_type': 'pdf',
                            'published_date': 'pre-2024',  # Mark PDFs as older content
                            'page': page_num,
                            'chunk_index': chunk_idx
                        }
                    })
        
        logger.info(f"Created {len(all_chunks)} text chunks from all documents")
        return all_chunks

    def process_web_article(self, article_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a web article into searchable chunks

        Args:
            article_data: Dict with keys: url, title, content, published_date, section

        Returns:
            List of chunks with metadata
        """
        try:
            url = article_data['url']
            title = article_data.get('title', 'Untitled')
            content = article_data.get('content', '')
            pub_date = article_data.get('published_date', 'Unknown')
            section = article_data.get('section', 'article')

            # Clean the content
            content = self._clean_text(content)

            # Create chunks
            text_chunks = self.chunk_text(content)

            # Build chunk objects with metadata
            chunks = []
            for chunk_idx, chunk_text in enumerate(text_chunks):
                chunk_id = f"web_{section}_{url.split('/')[-1]}_{chunk_idx}"

                chunks.append({
                    'text': chunk_text,
                    'filename': title,  # Use title as filename for display
                    'page_number': 0,  # Web articles use 0 instead of None
                    'chunk_id': chunk_id,
                    'metadata': {
                        'source': title,
                        'source_type': 'web',
                        'url': url,
                        'published_date': pub_date,
                        'section': section,
                        'chunk_index': chunk_idx
                    }
                })

            logger.info(f"Created {len(chunks)} chunks from web article: {title}")
            return chunks

        except Exception as e:
            logger.error(f"Error processing web article: {e}")
            return []

    def process_multiple_web_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple web articles into searchable chunks

        Args:
            articles: List of article data dicts

        Returns:
            List of all chunks from all articles
        """
        all_chunks = []

        for article in articles:
            chunks = self.process_web_article(article)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(articles)} web articles into {len(all_chunks)} total chunks")
        return all_chunks