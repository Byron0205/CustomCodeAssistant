"""
Proveedor OpenAI — LLM y embeddings en la nube.
Requiere OPENAI_API_KEY en .env
"""

from src.config import LLM_MODEL, EMBED_MODEL, OPENAI_API_KEY


def _check_key():
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY no está configurada. "
            "Agrega OPENAI_API_KEY=sk-... en tu .env"
        )


def _check_import():
    try:
        import langchain_openai  # noqa: F401
    except ImportError:
        raise ImportError(
            "langchain-openai no está instalado. "
            "Ejecuta: pipenv install langchain-openai"
        )


def get_llm():
    _check_key()
    _check_import()
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )


def get_embeddings():
    _check_key()
    _check_import()
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=EMBED_MODEL,
        api_key=OPENAI_API_KEY,
    )
