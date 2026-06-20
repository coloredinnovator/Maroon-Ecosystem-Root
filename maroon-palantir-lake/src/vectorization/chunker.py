"""
NASA-Grade Text Chunking Engine for Palantir Lake
Uses RecursiveCharacterTextSplitter for optimal semantic boundary retention.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Chunker] %(message)s')

class ChunkerConfig(BaseModel):
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=200, ge=0)

class ChunkerEngine:
    def __init__(self, config: ChunkerConfig = ChunkerConfig()):
        self.config = config
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Splits a single document into overlapping chunks with preserved metadata."""
        if not text.strip():
            return []
            
        try:
            chunks = self.splitter.split_text(text)
            
            # Reconstruct with metadata
            chunk_records = []
            for idx, chunk in enumerate(chunks):
                chunk_meta = dict(metadata) if metadata else {}
                chunk_meta.update({
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                })
                chunk_records.append({
                    "content": chunk,
                    "metadata": chunk_meta
                })
            return chunk_records
        except Exception as e:
            logging.error(f"Error chunking document: {e}")
            return []
