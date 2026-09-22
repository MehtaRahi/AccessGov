import json
import logging
import os

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import chromadb
import traceback

def ingest():
    try:
        print("1. Initializing embeddings...")
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        print("2. Connecting to ChromaDB on localhost:8080...")
        chroma_client = chromadb.HttpClient(host="localhost", port=8080)
        
        print("3. Instantiating Langchain Chroma object...")
        vector_store = Chroma(
            client=chroma_client,
            collection_name="accessgov_docs_llama3",
            embedding_function=embeddings,
        )
        
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/processed/processed_chunks.json"))
        print(f"4. Loading chunks from {path}")
        with open(path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        texts = chunks
        if not texts:
            print("No texts found!")
            return
            
        print(f"5. Found {len(texts)} chunks. Ingesting in batches of 5...")
        batch_size = 5
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            metadatas = [{"source": "manual_upload"} for _ in batch_texts]
            vector_store.add_texts(texts=batch_texts, metadatas=metadatas)
            print(f"✅ Ingested batch {i//batch_size + 1} of {total_batches}", flush=True)
            
        print("🎉 INGESTION COMPLETE!")
    except Exception as e:
        print("\n❌ CRASH DETECTED!")
        traceback.print_exc()

if __name__ == "__main__":
    ingest()
