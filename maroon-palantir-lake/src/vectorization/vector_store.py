"""
NASA-Grade Vector Store for Palantir Lake
Uses ChromaDB for local, ultra-fast embedding storage. This is the "Silver Layer".
"""
import os
import chromadb
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Vector Store] %(message)s')

class VectorStore:
    def __init__(self, persist_directory: str, collection_name: str = "palantir_lake_silver"):
        self.persist_directory = persist_directory
        
        # Ensure persistence directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logging.info(f"Initializing ChromaDB client at {self.persist_directory}")
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # Optimize for semantic similarity
        )
        
    def add_batch(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Fault-tolerant batch insertion into ChromaDB."""
        try:
            # ChromaDB expects dict values to be str, int, float or bool. 
            # We must sanitize metadata to prevent Pydantic or nested dictionary insertion errors.
            sanitized_metadatas = []
            for meta in metadatas:
                clean_meta = {}
                for k, v in meta.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    elif v is None:
                        continue # ChromaDB rejects None values in metadata
                    else:
                        clean_meta[k] = str(v)
                sanitized_metadatas.append(clean_meta)

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=sanitized_metadatas
            )
            logging.info(f"Successfully upserted batch of {len(ids)} vectors into ChromaDB.")
        except Exception as e:
            logging.error(f"Failed to upsert batch into ChromaDB: {e}")
            raise

    def get_collection_count(self) -> int:
        return self.collection.count()
