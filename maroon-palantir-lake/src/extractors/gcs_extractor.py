import logging
from typing import List, Dict, Any
from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure NASA-grade logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [GCS Extractor] %(message)s')

class GCSNetworkError(Exception):
    pass

class GCSExtractor:
    def __init__(self, target_buckets: List[str] = None):
        self.client = storage.Client()
        self.target_buckets = target_buckets or ["marooncleanup"]
        
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(GCSNetworkError),
        reraise=True
    )
    def _download_blob_bytes_with_retry(self, blob) -> bytes:
        """NASA-grade fault-tolerant download with exponential backoff."""
        try:
            return blob.download_as_bytes()
        except Exception as e:
            logging.warning(f"Network error downloading {blob.name}: {e}. Retrying...")
            raise GCSNetworkError(f"Failed to download {blob.name}") from e

    def extract_text_from_blob(self, blob) -> str:
        """Extract text robustly, decoding bytes explicitly to handle encoding errors."""
        ext = blob.name.split('.')[-1].lower() if '.' in blob.name else ''
        text_extensions = frozenset({'txt', 'md', 'json', 'py', 'sh', 'js', 'html', 'csv', 'yaml', 'yml'})
        
        if ext in text_extensions:
            try:
                raw_bytes = self._download_blob_bytes_with_retry(blob)
                return raw_bytes.decode('utf-8', errors='ignore')
            except Exception as e:
                logging.error(f"CRITICAL: Failed to read text from {blob.name} after retries: {e}")
                return ""
        elif ext == 'pdf':
            return f"[PDF Data: {blob.size} bytes]"
        return f"[Binary Data: {blob.size} bytes]"

    def crawl_and_extract(self) -> List[Dict[str, Any]]:
        """Crawls target buckets and returns a list of raw documents."""
        documents = []
        for bucket_name in self.target_buckets:
            logging.info(f"Scanning bucket: {bucket_name}")
            try:
                bucket = self.client.bucket(bucket_name)
                blobs = bucket.list_blobs()
                for blob in blobs:
                    logging.info(f"Extracting {blob.name} ({blob.size} bytes)")
                    content = self.extract_text_from_blob(blob)
                    if content:
                        documents.append({
                            "source_type": "gcs",
                            "source_uri": f"gs://{bucket_name}/{blob.name}",
                            "content": content,
                            "metadata": {
                                "content_type": blob.content_type,
                                "updated": blob.updated.isoformat() if blob.updated else None,
                                "size": blob.size
                            }
                        })
            except Exception as e:
                logging.error(f"Error accessing bucket {bucket_name}: {e}")
        
        logging.info(f"Extracted {len(documents)} documents from GCS.")
        return documents

if __name__ == "__main__":
    extractor = GCSExtractor(["marooncleanup"])
    docs = extractor.crawl_and_extract()
    print(f"Sample extraction: Found {len(docs)} files.")
