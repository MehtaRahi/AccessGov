import os
import httpx
from langchain_openai import ChatOpenAI


def get_llm():
    """
    Returns a LangChain LLM instance.
    Supports Groq (default) and OpenAI cloud providers.
    All Ollama/local model references have been removed.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    # Bypass SSL verification for httpx (used by ChatOpenAI/openai-python)
    http_client = httpx.Client(verify=False)

    if provider == "groq":
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            api_key=os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client
        )
    elif provider == "openai":
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY", ""),
            http_client=http_client
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: groq, openai")
