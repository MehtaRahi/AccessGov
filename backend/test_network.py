import requests
import traceback

def test_ollama():
    print("Testing connection to Ollama at host.docker.internal...")
    try:
        resp = requests.get("http://host.docker.internal:11434/api/tags", timeout=5)
        print("✅ SUCCESS! Connected to Ollama.")
        print(resp.json())
    except Exception as e:
        print("❌ FAILED to connect to Ollama.")
        traceback.print_exc()

def test_chroma():
    print("\nTesting connection to ChromaDB...")
    try:
        resp = requests.get("http://chromadb:8000/api/v1", timeout=5)
        print("✅ SUCCESS! Connected to ChromaDB.")
    except Exception as e:
        print("❌ FAILED to connect to ChromaDB.")
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama()
    test_chroma()
