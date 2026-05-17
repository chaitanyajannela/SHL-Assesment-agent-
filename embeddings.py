"""Vector embeddings management for RAG retrieval."""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import hashlib


class EmbeddingManager:
    """Manages document embeddings for assessment retrieval."""
    
    def __init__(self, collection_name: str = "shl_assessments", persist_directory: str = "chroma_db"):
        """
        Initialize embedding manager.
        
        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory for persistent storage
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.embedding_fn = None
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and embedding function."""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            print(f"Warning: Could not initialize ChromaDB: {e}")
            self.client = None
    
    def create_collection(self) -> None:
        """Create or get existing collection."""
        if not self.client:
            return
        
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print(f"Using existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )
            print(f"Created new collection: {self.collection_name}")
    
    def create_document_text(self, assessment: Dict[str, Any]) -> str:
        """
        Create searchable document text from assessment.
        
        Args:
            assessment: Assessment dictionary
            
        Returns:
            Text representation for embedding
        """
        parts = [
            f"Name: {assessment.get('name', '')}",
            f"Type: {assessment.get('test_type', '')}",
        ]
        
        # Add keys/categories
        keys = assessment.get('keys', [])
        if keys:
            parts.append(f"Categories: {', '.join(keys)}")
        
        # Add job levels
        job_levels = assessment.get('job_levels', [])
        if job_levels:
            parts.append(f"Job Levels: {', '.join(job_levels)}")
        
        # Add description
        description = assessment.get('description', '')
        if description:
            parts.append(f"Description: {description[:500]}")
        
        return " | ".join(parts)
    
    def index_assessments(self, assessments: List[Dict[str, Any]]) -> int:
        """
        Index assessments in vector database.
        
        Args:
            assessments: List of assessment dictionaries
            
        Returns:
            Number of successfully indexed assessments
        """
        if not self.collection or not assessments:
            return 0
        
        documents = []
        metadatas = []
        ids = []
        
        for assessment in assessments:
            doc_text = self.create_document_text(assessment)
            documents.append(doc_text)
            metadatas.append(assessment)
            
            # Create stable ID from entity_id or name
            entity_id = assessment.get('entity_id', assessment.get('id', ''))
            doc_id = hashlib.md5(f"{entity_id}_{assessment.get('name', '')}".encode()).hexdigest()[:16]
            ids.append(doc_id)
        
        try:
            # Add in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                self.collection.add(
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
            return len(ids)
        except Exception as e:
            print(f"Error indexing assessments: {e}")
            return 0
    
    def search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar assessments.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of matching assessments
        """
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                return results['metadatas'][0]
        except Exception as e:
            print(f"Search error: {e}")
        
        return []