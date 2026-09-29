import json
import logging
import os

from langchain_community.vectorstores import Chroma
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a NEW collection name to avoid dimension mismatch with old Ollama embeddings
COLLECTION_NAME = "accessgov_docs_v2"


from langchain_core.embeddings import Embeddings

class FakeEmbeddings(Embeddings):
    """Dummy embeddings to bypass local ML models that cause segfaults/OOM on weak machines."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 384 for _ in texts]
        
    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 384

class VectorStoreManager:
    def __init__(self, chroma_host: str = "chromadb", chroma_port: int = 8000):
        # Using FakeEmbeddings temporarily to prevent native library crashes
        self.embeddings = FakeEmbeddings()
        
        # Connect to ChromaDB (running via Docker)
        chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self.vector_store = Chroma(
            client=chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
        )
        logger.info(f"✅ Connected to ChromaDB at {chroma_host}:{chroma_port} (collection: {COLLECTION_NAME})")

    def delete_document_chunks(self, source_filename: str):
        """Purges all chunks associated with a specific source document."""
        try:
            logger.info(f"Purging old chunks for {source_filename} from ChromaDB...")
            collection = self.vector_store._collection
            collection.delete(where={"source": source_filename})
            logger.info(f"✅ Deleted old chunks for {source_filename}.")
        except Exception as e:
            logger.error(f"Failed to delete chunks for {source_filename}: {e}")

    def ingest_data(self, json_path: str):
        if self.vector_store is None:
            raise ValueError("❌ Vector store is not initialized.")

        logger.info(f"⏳ Loading chunks from {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        if chunks:
            # 1. Purge old chunks for any documents we are about to ingest
            unique_sources = set(c.get("source") for c in chunks if c.get("source"))
            for source in unique_sources:
                self.delete_document_chunks(source)

            logger.info(f"🚀 Ingesting {len(chunks)} chunks into ChromaDB in batches of 10...")
            batch_size = 10
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                batch_texts = [c["text"] for c in batch_chunks]
                batch_metadatas = [{"source": c.get("source", "unknown"), "chunk_id": c.get("id", str(idx))} for idx, c in enumerate(batch_chunks)]
                
                self.vector_store.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                logger.info(f"✅ Batch {i//batch_size + 1}/{total_batches}")
                
            logger.info("✅ Ingestion complete.")
        else:
            logger.warning("⚠️ No texts found to ingest.")

if __name__ == "__main__":
    manager = VectorStoreManager()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/processed/processed_chunks.json"))
    print(f"🔍 Looking for data at: {path}")
    if os.path.exists(path):
        manager.ingest_data(path)
    else:
        print(f"❌ Path not found: {path}")
