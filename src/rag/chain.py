"""
Construcción centralizada del RAG chain.
Consolida la lógica que estaba duplicada en consultar.py y evaluar.py.
"""

import sys
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

from src.config import (
    CHROMA_PATH,
    EMBED_MODEL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
    RETRIEVER_K,
    RAG_MODES,
    DEFAULT_MODE,
)


def build_chain(mode: str = DEFAULT_MODE):
    """
    Construye y retorna la cadena RetrievalQA completa.
    Consolida: embeddings + vectorstore + LLM + prompt + retriever
    """
    if mode not in RAG_MODES:
        raise ValueError(f"Modo desconocido: '{mode}'. Usa /modes para ver los disponibles.")

    try:
        embeddings = OllamaEmbeddings(
            model=EMBED_MODEL,
            base_url=OLLAMA_BASE_URL
        )

        vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )

        llm = OllamaLLM(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1
        )

        prompt = PromptTemplate(
            template=RAG_MODES[mode]["prompt_template"],
            input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K}),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        return qa_chain

    except Exception as e:
        print(f"[ERROR] Error al cargar el RAG: {e}")
        print("[!] ¿Ollama está corriendo? ¿ChromaDB fue indexado?")
        sys.exit(1)
