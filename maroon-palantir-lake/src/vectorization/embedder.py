"""
NASA-Grade Embedding Engine for Palantir Lake
Local, open-source embeddings via HuggingFace Sentence Transformers to preserve zero-cost, sovereign operations.
"""
from typing import List
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Embedder] %(message)s')

class EmbeddingEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logging.info(f"Loading embedding model: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name)
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load model {model_name}: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Converts a batch of texts into highly dimensional vectors."""
        if not texts:
            return []
        
        try:
            # Output is a NumPy array, convert to standard Python floats for database persistence
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logging.error(f"Failed to embed texts: {e}")
            raise
