import os
import shutil
import logging
import datetime
from app.services.document_parser import DocumentParser
from app.services.vector_store import VectorStoreManager
from app.services.scraper import GovScraper

# Config will be loaded dynamically

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline():
    """
    Executes the automated data pipeline:
    1. Scans data/raw for new PDFs/TXTs
    2. Parses & chunks them
    3. Ingests into ChromaDB
    4. Moves processed files to data/archive to prevent duplicate ingestion
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/crawler_config.json"))
    raw_dir = os.path.join(base_dir, "raw")
    processed_dir = os.path.join(base_dir, "processed")
    archive_dir = os.path.join(base_dir, "archive")
    json_path = os.path.join(processed_dir, "processed_chunks.json")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    # Load dynamic config
    seed_urls = []
    max_depth = 1
    download_limit = 5
    if os.path.exists(config_path):
        import json
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                seed_urls = config.get("seed_urls", [])
                max_depth = config.get("max_depth", 1)
                download_limit = config.get("download_limit", 5)
        except Exception as e:
            logger.error(f"Failed to read config: {e}")

    # 1. Scrape for new PDFs from seed URLs
    logger.info(f"[{datetime.datetime.now()}] Data Pipeline: Starting web scraper for seed URLs...")
    scraper = GovScraper(output_dir=raw_dir)
    for url in seed_urls:
        scraper.download_pdfs_from_url(url, archive_dir=archive_dir, limit=download_limit, max_depth=max_depth)

    # 2. Check if there are any files to process
    files_to_process = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.pdf', '.txt'))]
    if not files_to_process:
        logger.info(f"[{datetime.datetime.now()}] Data Pipeline: No new documents found in {raw_dir}.")
        return {"status": "skipped", "message": "No new documents to process."}

    logger.info(f"[{datetime.datetime.now()}] Data Pipeline: Found {len(files_to_process)} new documents. Starting processing...")

    # 2. Parse and chunk
    parser = DocumentParser(raw_dir=raw_dir, processed_dir=processed_dir)
    parser.process_all_documents()

    if not os.path.exists(json_path):
        logger.error("Data Pipeline: Parser ran but no processed_chunks.json was created.")
        return {"status": "error", "message": "Failed to generate chunks."}

    # 3. Ingest into ChromaDB
    try:
        # Note: VectorStoreManager defaults to "chromadb" for docker network, change to "localhost" if running outside
        # But this script runs inside the backend container via APScheduler, so "chromadb" is correct.
        manager = VectorStoreManager(chroma_host="chromadb") 
        manager.ingest_data(json_path)
    except Exception as e:
        logger.error(f"Data Pipeline: Vector store ingestion failed: {e}")
        return {"status": "error", "message": f"Ingestion failed: {e}"}

    # 4. Archive processed files
    for filename in files_to_process:
        src = os.path.join(raw_dir, filename)
        dst = os.path.join(archive_dir, f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        try:
            shutil.move(src, dst)
            logger.info(f"Moved {filename} to archive.")
        except Exception as e:
            logger.error(f"Failed to move {filename} to archive: {e}")

    # Remove the chunks file so we don't accidentally re-ingest old chunks next time
    try:
        os.remove(json_path)
    except:
        pass

    logger.info(f"[{datetime.datetime.now()}] Data Pipeline: Successfully completed processing {len(files_to_process)} documents.")
    return {"status": "success", "message": f"Processed and ingested {len(files_to_process)} documents."}

if __name__ == "__main__":
    run_pipeline()
