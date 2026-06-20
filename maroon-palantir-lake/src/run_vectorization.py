import os
import sys
import json
import logging
from typing import Iterator, Dict, Any
import hashlib

# Add parent directory to path to allow importing from src.vectorization
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vectorization.chunker import ChunkerEngine
from src.vectorization.embedder import EmbeddingEngine
from src.vectorization.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Vectorization Orchestrator] %(message)s')

def jsonl_reader(file_path: str) -> Iterator[Dict[str, Any]]:
    """Streams JSONL lines to keep memory footprint minimal."""
    if not os.path.exists(file_path):
        logging.error(f"Bronze file not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    logging.warning("Skipped malformed JSON line.")

def run_state_2_pipeline(bronze_file: str, batch_size: int = 50):
    """Executes the State 2 Vectorization Pipeline."""
    logging.info(f"Igniting State 2: Vectorization of {bronze_file}")
    
    # Initialize Engines
    chunker = ChunkerEngine()
    embedder = EmbeddingEngine()
    
    silver_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "silver_vectors")
    store = VectorStore(persist_directory=silver_dir)
    
    batch_texts = []
    batch_metadatas = []
    batch_ids = []
    documents_processed = 0
    chunks_created = 0

    for doc in jsonl_reader(bronze_file):
        content = doc.get("content", "")
        if not content or content.startswith("[Binary Data") or content.startswith("[PDF Data"):
            continue # Skip unreadable binary placeholders
            
        metadata = doc.get("metadata", {})
        metadata["source_uri"] = doc.get("source_uri", "unknown")
        
        # 1. Chunk
        chunks = chunker.chunk_document(content, metadata)
        if not chunks:
            continue
            
        for chunk in chunks:
            text = chunk["content"]
            meta = chunk["metadata"]
            
            # Generate deterministic ID
            hash_id = hashlib.sha256(f"{meta['source_uri']}_{meta['chunk_index']}".encode()).hexdigest()
            
            batch_texts.append(text)
            batch_metadatas.append(meta)
            batch_ids.append(hash_id)
            chunks_created += 1
            
            # Flush batch
            if len(batch_texts) >= batch_size:
                embeddings = embedder.embed_texts(batch_texts)
                store.add_batch(ids=batch_ids, embeddings=embeddings, documents=batch_texts, metadatas=batch_metadatas)
                
                # Reset batch
                batch_texts = []
                batch_metadatas = []
                batch_ids = []
                
        documents_processed += 1
        if documents_processed % 100 == 0:
            logging.info(f"Processed {documents_processed} documents. ChromaDB collection size: {store.get_collection_count()}")

    # Flush remaining
    if batch_texts:
        embeddings = embedder.embed_texts(batch_texts)
        store.add_batch(ids=batch_ids, embeddings=embeddings, documents=batch_texts, metadatas=batch_metadatas)
        
    logging.info(f"State 2 Complete! Processed {documents_processed} documents into {chunks_created} vectors.")
    logging.info(f"Final Silver Layer Vector Count: {store.get_collection_count()}")

if __name__ == "__main__":
    import glob
    bronze_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "bronze")
    jsonl_files = glob.glob(os.path.join(bronze_dir, "*.jsonl"))
    
    if not jsonl_files:
        logging.error("No JSONL files found in the Bronze layer.")
    else:
        # Sort by creation time to process the latest one
        latest_bronze = max(jsonl_files, key=os.path.getctime)
        # We will set a smaller batch size (e.g. 100) to keep memory safe during embedding
        run_state_2_pipeline(latest_bronze, batch_size=100)
