from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingService:
    """Service to handle text chunking and vector embeddings."""
    
    def __init__(self):
        # We use a fast, lightweight open-source embedding model by default
        self.embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Splits raw text into smaller chunks for vectorization."""
        chunks = self.text_splitter.create_documents([text], metadatas=[metadata or {}])
        
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "chunk_index": i,
                "content": chunk.page_content,
                "metadata": chunk.metadata
            })
        return result

    def embed_text(self, text: str) -> List[float]:
        """Generates a vector embedding for a single string of text."""
        return self.embeddings_model.embed_query(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a list of strings."""
        return self.embeddings_model.embed_documents(texts)
