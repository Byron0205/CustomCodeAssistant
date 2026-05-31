"""
Proveedor Ollama — LLM local y embeddings locales.
Requiere Ollama corriendo en OLLAMA_BASE_URL.
"""

from langchain_ollama import OllamaEmbeddings, OllamaLLM
from src.config import EMBED_MODEL, LLM_MODEL, OLLAMA_BASE_URL


def get_llm():
    return OllamaLLM(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )


def get_embeddings():
    return OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
