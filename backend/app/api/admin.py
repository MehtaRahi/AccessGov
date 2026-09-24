from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import logging
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)

# Paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
archive_dir = os.path.join(base_dir, "archive")
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/config/crawler_config.json"))

class CrawlerConfig(BaseModel):
    seed_urls: List[str]
    max_depth: int
    download_limit: int

@router.get("/config")
def get_config():
    if not os.path.exists(config_path):
        return {"seed_urls": [], "max_depth": 1, "download_limit": 5}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.post("/config")
def update_config(config: CrawlerConfig):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.dict(), f, indent=2)
    return {"status": "success", "message": "Configuration updated."}

@router.get("/documents")
def list_documents():
    if not os.path.exists(archive_dir):
        return []
    
    docs = []
    for file in os.listdir(archive_dir):
        if file.endswith(('.pdf', '.txt')):
            path = os.path.join(archive_dir, file)
            # Extract date (YYYYMMDDHHMMSS_filename)
            parts = file.split("_", 1)
            date_ingested = parts[0] if len(parts) > 1 else "Unknown"
            original_name = parts[1] if len(parts) > 1 else file
            
            docs.append({
                "archive_name": file,
                "original_name": original_name,
                "date_ingested": date_ingested,
                "size_kb": round(os.path.getsize(path) / 1024, 2)
            })
    return sorted(docs, key=lambda x: x["date_ingested"], reverse=True)

@router.delete("/documents/{filename}")
def delete_document(filename: str):
    # 1. Delete from Vector Store
    from app.services.vector_store import VectorStoreManager
    try:
        manager = VectorStoreManager(chroma_host="chromadb")
        parts = filename.split("_", 1)
        original_name = parts[1] if len(parts) > 1 else filename
        manager.delete_document_chunks(original_name)
    except Exception as e:
        logger.error(f"Failed to purge chunks for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    # 2. Delete the physical file
    file_path = os.path.join(archive_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return {"status": "success", "message": f"Deleted {original_name} from vector store and archive."}
