import os
from typing import List, Dict, Any
from langchain_postgres import PGVector
from langchain_core.documents import Document as LCDocument
from app.core.config import settings
from app.services.embedding_service import EmbeddingService

class VectorStoreService:
    """Service to handle pgvector storage and semantic search."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.connection_string = settings.DATABASE_URI
        # Ensure driver is psycopg for langchain-postgres compatibility
        if self.connection_string.startswith("postgresql://"):
            self.connection_string = self.connection_string.replace("postgresql://", "postgresql+psycopg://", 1)
        elif self.connection_string.startswith("postgresql+asyncpg://"):
            self.connection_string = self.connection_string.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
            
        # psycopg doesn't like '?ssl=require', it expects sslmode
        if "?ssl=" in self.connection_string:
            self.connection_string = self.connection_string.split("?ssl=")[0]

        self.collection_name = "orbitos_knowledge_base"
        
        self.vector_store = PGVector(
            embeddings=self.embedding_service.embeddings_model,
            collection_name=self.collection_name,
            connection=self.connection_string,
            use_jsonb=True,
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Adds text chunks to the vector database."""
        docs = []
        for chunk in chunks:
            docs.append(LCDocument(
                page_content=chunk["content"],
                metadata=chunk["metadata"]
            ))
        
        # This creates tables if they don't exist and inserts vectors
        self.vector_store.add_documents(docs)

    def search(self, query: str, top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Performs a semantic search with optional metadata filtering."""
        
        results = self.vector_store.similarity_search_with_score(
            query=query, 
            k=top_k, 
            filter=filter_dict
        )
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
            
        return formatted_results
