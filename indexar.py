#!/usr/bin/env python3
"""
Entry point: Indexación de documentos.
Delega la lógica a src/rag/loader.py
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from src.config import (
    CHROMA_PATH, CHUNK_SIZE, CHUNK_OVERLAP, LLM_PROVIDER, EMBED_PROVIDER, EMBED_MODEL
)
from src.rag.loader import load_all_documents
from src.providers import get_embeddings


def main():
    print(f"[>>] Proveedor de embeddings: {EMBED_PROVIDER} ({EMBED_MODEL})")
    print("[>>] Cargando documentos...")
    docs = load_all_documents()
    print(f"[OK] Documentos cargados: {len(docs)}")

    print("[>>] Dividiendo en chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=['\n\n', '\n', ' ', '']
    )
    chunks = splitter.split_documents(docs)
    print(f"[OK] Chunks generados: {len(chunks)}")

    print("[>>] Generando embeddings...")
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )
    print(f"[OK] Indexación completa. Base de datos guardada en: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
