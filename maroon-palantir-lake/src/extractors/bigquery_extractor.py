import logging
from typing import List, Dict, Any
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json

# NASA-grade logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [BigQuery Extractor] %(message)s')

class BigQueryExtractor:
    def __init__(self, projects: List[str] = None):
        self.projects = projects or ["coloredinnovator", "maroon-clean-up"]

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True
    )
    def _fetch_rows_with_retry(self, client: bigquery.Client, table_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """NASA-grade fault-tolerant table extraction with exponential backoff."""
        try:
            rows = client.list_rows(table_id, max_results=limit)
            return [dict(row.items()) for row in rows]
        except GoogleAPIError as e:
            logging.warning(f"API Error extracting table {table_id}: {e}. Retrying...")
            raise e

    def extract_all(self) -> List[Dict[str, Any]]:
        documents = []
        for project in self.projects:
            logging.info(f"Scanning BigQuery in project: {project}")
            try:
                client = bigquery.Client(project=project)
                datasets = list(client.list_datasets())
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset.dataset_id))
                    for table in tables:
                        table_id = f"{project}.{dataset.dataset_id}.{table.table_id}"
                        logging.info(f"Extracting table: {table_id}")
                        
                        try:
                            # Safely fetch rows with backoff
                            data = self._fetch_rows_with_retry(client, table_id, limit=1000)
                            
                            if data:
                                documents.append({
                                    "source_type": "bigquery",
                                    "source_uri": f"bq://{table_id}",
                                    "content": json.dumps(data, default=str),
                                    "metadata": {
                                        "project": project,
                                        "dataset": dataset.dataset_id,
                                        "table": table.table_id,
                                        "row_count_extracted": len(data)
                                    }
                                })
                        except Exception as e:
                            logging.error(f"CRITICAL: Failed to read table {table_id} after retries: {e}")
                            
            except Exception as e:
                logging.error(f"Error accessing BigQuery in project {project}: {e}")
                
        logging.info(f"Extracted {len(documents)} table snapshots from BigQuery.")
        return documents

if __name__ == "__main__":
    extractor = BigQueryExtractor()
    docs = extractor.extract_all()
    print(f"Sample extraction: Found {len(docs)} tables.")
