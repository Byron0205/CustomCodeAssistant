"""
Factory de proveedores LLM y embeddings.
Selecciona la implementación según LLM_PROVIDER y EMBED_PROVIDER en .env
"""

from src.config import LLM_PROVIDER, EMBED_PROVIDER


def get_llm():
    if LLM_PROVIDER == "ollama":
        from src.providers.ollama import get_llm as _fn
    elif LLM_PROVIDER == "claude":
        from src.providers.claude import get_llm as _fn
    elif LLM_PROVIDER == "openai":
        from src.providers.openai_provider import get_llm as _fn
    else:
        raise ValueError(
            f"LLM_PROVIDER desconocido: '{LLM_PROVIDER}'. "
            "Opciones válidas: ollama, claude, openai"
        )
    return _fn()


def get_embeddings():
    if EMBED_PROVIDER == "ollama":
        from src.providers.ollama import get_embeddings as _fn
    elif EMBED_PROVIDER == "openai":
        from src.providers.openai_provider import get_embeddings as _fn
    else:
        raise ValueError(
            f"EMBED_PROVIDER desconocido: '{EMBED_PROVIDER}'. "
            "Opciones válidas: ollama, openai — Claude no tiene embeddings propios."
        )
    return _fn()
