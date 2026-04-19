#!/usr/bin/env python3
"""
Entry point: Indexación de documentos.
Delega la lógica a src/rag/loader.py
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from src.config import (
    CHROMA_PATH, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
)
from src.rag.loader import load_all_documents


def main():
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
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f"[OK] Indexacion completa. Base de datos guardada en: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
