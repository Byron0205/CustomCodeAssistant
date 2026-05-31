"""
Construcción centralizada del RAG chain.
Usa el factory de providers para soportar Ollama, Claude y OpenAI.
"""

import sys
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

from src.config import CHROMA_PATH, RETRIEVER_K, RAG_MODES, DEFAULT_MODE, LLM_PROVIDER, EMBED_PROVIDER
from src.providers import get_llm, get_embeddings


def load_vectorstore():
    """
    Carga el vectorstore sin construir el chain completo.
    Usar en consultar.py para separar retrieval de generación (streaming).
    """
    try:
        embeddings = get_embeddings()
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    except (ValueError, NotImplementedError) as e:
        print(f"[ERROR] Configuración de proveedor: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error al cargar vectorstore: {e}")
        print("[!] ¿ChromaDB fue indexado? Ejecuta: pipenv run python indexar.py")
        sys.exit(1)


def build_chain(mode: str = DEFAULT_MODE):
    """
    Construye y retorna la cadena RetrievalQA completa.
    El LLM y los embeddings se resuelven desde src/providers/ según .env
    """
    if mode not in RAG_MODES:
        raise ValueError(f"Modo desconocido: '{mode}'. Usa /modes para ver los disponibles.")

    try:
        embeddings = get_embeddings()
        vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
        )
        llm = get_llm()

        prompt = PromptTemplate(
            template=RAG_MODES[mode]["prompt_template"],
            input_variables=["context", "question"],
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K}),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )

        return qa_chain

    except (ValueError, NotImplementedError) as e:
        print(f"[ERROR] Configuración de proveedor: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error al cargar el RAG: {e}")
        print(f"[!] LLM_PROVIDER={LLM_PROVIDER} | EMBED_PROVIDER={EMBED_PROVIDER}")
        print("[!] ¿Ollama está corriendo? ¿ChromaDB fue indexado? ¿API key configurada?")
        sys.exit(1)
