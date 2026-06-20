import asyncio
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Local Extractors
from extractors.gcs_extractor import GCSExtractor
from extractors.bigquery_extractor import BigQueryExtractor
from extractors.drive_docs_extractor import DriveDocsExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class IngestionOrchestrator:
    def __init__(self):
        self.gcs_extractor = GCSExtractor()
        self.bq_extractor = BigQueryExtractor()
        self.drive_extractor = DriveDocsExtractor()
        
        # In a real scenario, this connects to the Palantir Lake Postgres (Bronze Layer)
        # For this script, we'll write to a massive local JSONL file as the "Bronze File Sink"
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "bronze")
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, f"bronze_ingress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

    def _flush_to_bronze(self, documents: List[Dict[str, Any]]):
        """Appends extracted documents to the Bronze storage layer."""
        with open(self.output_file, 'a', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc) + '\n')
        logging.info(f"Flushed {len(documents)} records to Bronze Layer ({self.output_file})")

    async def run(self):
        logging.info("Starting State 1 Massive Ingestion...")
        
        # 1. Google Drive / AI Studio
        logging.info("--- Extracting Google Drive / AI Studio ---")
        drive_docs = self.drive_extractor.extract_all()
        if drive_docs:
            self._flush_to_bronze(drive_docs)

        # 2. BigQuery Datasets
        logging.info("--- Extracting BigQuery Datasets ---")
        # We run synchronous GCP calls in executor to avoid blocking event loop
        bq_docs = await asyncio.to_thread(self.bq_extractor.extract_all)
        if bq_docs:
            self._flush_to_bronze(bq_docs)

        # 3. GCS Bucket (The large 5 million token payload)
        logging.info("--- Extracting GCS Bucket (marooncleanup) ---")
        gcs_docs = await asyncio.to_thread(self.gcs_extractor.crawl_and_extract)
        if gcs_docs:
            self._flush_to_bronze(gcs_docs)

        logging.info("State 1 Ingestion Complete. All raw data is safely inside the Palantir Lake Bronze layer.")

if __name__ == "__main__":
    orchestrator = IngestionOrchestrator()
    asyncio.run(orchestrator.run())
