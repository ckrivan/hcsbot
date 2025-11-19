import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="apple_pdfs",
                metadata={"description": "Apple technology PDF documents"}
            )
            
            logger.info(f"ChromaDB initialized at {self.db_path}")
            logger.info(f"Collection has {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to the vector database"""
        try:
            if not chunks:
                logger.warning("No chunks to add to database")
                return
            
            # Extract texts and metadata
            texts = [chunk['text'] for chunk in chunks]
            ids = [chunk['chunk_id'] for chunk in chunks]
            
            # Prepare metadata for ChromaDB
            metadatas = []
            for chunk in chunks:
                metadata = {
                    'filename': chunk['filename'],
                    'page_number': str(chunk['page_number']),
                    'chunk_index': str(chunk['metadata']['chunk_index'])
                }
                metadatas.append(metadata)
            
            # Generate embeddings
            logger.info("Generating embeddings for document chunks...")
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add to ChromaDB
            logger.info(f"Adding {len(chunks)} chunks to vector database...")
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} documents to vector database")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {e}")
            raise
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents based on query"""
        try:
            # Validate connection first
            if not self._validate_connection():
                logger.warning("Vector database connection invalid, attempting to reconnect...")
                self._initialize_db()
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'filename': results['metadatas'][0][i]['filename'],
                        'page_number': int(results['metadatas'][0][i]['page_number']),
                        'chunk_index': int(results['metadatas'][0][i]['chunk_index']),
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            logger.info(f"Found {len(formatted_results)} similar documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
            # Try to reconnect and retry once
            try:
                logger.info("Attempting to reconnect to vector database...")
                self._initialize_db()
                query_embedding = self.embedding_model.encode([query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
                
                formatted_results = []
                if results['documents'] and len(results['documents']) > 0:
                    for i in range(len(results['documents'][0])):
                        formatted_results.append({
                            'text': results['documents'][0][i],
                            'filename': results['metadatas'][0][i]['filename'],
                            'page_number': int(results['metadatas'][0][i]['page_number']),
                            'chunk_index': int(results['metadatas'][0][i]['chunk_index']),
                            'similarity_score': 1 - results['distances'][0][i]
                        })
                
                logger.info(f"Retry successful: Found {len(formatted_results)} similar documents")
                return formatted_results
                
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection.name,
                'db_path': self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Delete the collection
            self.client.delete_collection(name="apple_pdfs")
            
            # Recreate it
            self.collection = self.client.get_or_create_collection(
                name="apple_pdfs",
                metadata={"description": "Apple technology PDF documents"}
            )
            
            logger.info("Collection cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
    
    def _validate_connection(self) -> bool:
        """Validate that the database connection is working"""
        try:
            if not self.client or not self.collection:
                return False
            
            # Test a simple operation
            count = self.collection.count()
            return count >= 0
            
        except Exception as e:
            logger.warning(f"Database connection validation failed: {e}")
            return False