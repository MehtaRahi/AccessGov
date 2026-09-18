import json
import logging
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8080):
        # Use HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Connect to ChromaDB (running via Docker)
        try:
            chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            self.vector_store = Chroma(
                client=chroma_client,
                collection_name="accessgov_docs",
                embedding_function=self.embeddings,
            )
            logger.info(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            self.vector_store = None

    def ingest_data(self, json_path: str):
        if not self.vector_store:
            logger.error("Vector store is not initialized.")
            return

        logger.info(f"Loading chunks from {json_path}")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            texts = chunks
            if texts:
                logger.info(f"Ingesting {len(texts)} chunks into ChromaDB...")
                metadatas = [{"source": "manual_upload"} for _ in texts]
                self.vector_store.add_texts(texts=texts, metadatas=metadatas)
                logger.info("Ingestion complete.")
            else:
                logger.warning("No texts found to ingest.")
        except Exception as e:
            logger.error(f"Error reading {json_path}: {e}")

if __name__ == "__main__":
    import os
    manager = VectorStoreManager()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/processed/processed_chunks.json"))
    if os.path.exists(path):
        manager.ingest_data(path)
    else:
        logger.error(f"Path not found: {path}")
