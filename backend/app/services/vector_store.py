import json
import logging
import os

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, chroma_host: str = "chromadb", chroma_port: int = 8000):
        # Use local Ollama embeddings to completely bypass SSL/Proxy blocks!
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://host.docker.internal:11434"
        )
        
        # Connect to ChromaDB (running via Docker)
        chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self.vector_store = Chroma(
            client=chroma_client,
            collection_name="accessgov_docs_llama3",
            embedding_function=self.embeddings,
        )
        print(f"✅ Successfully connected to ChromaDB at {chroma_host}:{chroma_port}", flush=True)

    def ingest_data(self, json_path: str):
        if self.vector_store is None:
            raise ValueError("❌ Vector store is not initialized.")

        print(f"⏳ Loading chunks from {json_path}", flush=True)
        with open(json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        if chunks:
            print(f"🚀 Ingesting {len(chunks)} chunks into ChromaDB in batches of 5... this may take a while.", flush=True)
            batch_size = 5
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                
                # Extract text and metadata from the dictionary
                batch_texts = [c["text"] for c in batch_chunks]
                batch_metadatas = [{"source": c.get("source", "unknown"), "chunk_id": c.get("id", str(idx))} for idx, c in enumerate(batch_chunks)]
                
                self.vector_store.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                print(f"✅ Ingested batch {i//batch_size + 1} of {total_batches}", flush=True)
                
            print("✅ Ingestion complete.", flush=True)
        else:
            print("⚠️ No texts found to ingest.", flush=True)

if __name__ == "__main__":
    import os
    manager = VectorStoreManager()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/processed/processed_chunks.json"))
    print(f"🔍 Looking for data chunks at: {path}")
    if os.path.exists(path):
        manager.ingest_data(path)
    else:
        print(f"❌ Path not found: {path}")
