"""
Proveedor Claude (Anthropic) — solo LLM, sin embeddings.
Requiere ANTHROPIC_API_KEY en .env
"""

from src.config import LLM_MODEL, ANTHROPIC_API_KEY


def get_llm():
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY no está configurada. "
            "Agrega ANTHROPIC_API_KEY=sk-ant-... en tu .env"
        )

    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic no está instalado. "
            "Ejecuta: pipenv install langchain-anthropic"
        )

    return ChatAnthropic(
        model=LLM_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=0.1,
    )


def get_embeddings():
    raise NotImplementedError(
        "Claude no tiene API de embeddings. "
        "Usa EMBED_PROVIDER=ollama o EMBED_PROVIDER=openai en tu .env"
    )
