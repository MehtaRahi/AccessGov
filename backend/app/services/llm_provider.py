import os
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI

def get_llm():
    """
    Returns a LangChain LLM instance based on the configured provider.
    Allows easy swapping between local Ollama and a free/paid cloud API.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        return Ollama(
            model="llama3",
            base_url="http://host.docker.internal:11434"
        )
    elif provider == "openai":
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
