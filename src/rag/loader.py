"""
Cargador de documentos desde ./docs/
Soporta múltiples formatos: .md, .txt, .py, .pdf
"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader

from src.config import DOCS_PATH


def load_markdown_docs():
    """Carga documentos Markdown."""
    loader = DirectoryLoader(
        DOCS_PATH,
        glob='**/*.md',
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    return loader.load()


def load_text_docs():
    """Carga documentos de texto plano."""
    loader = DirectoryLoader(
        DOCS_PATH,
        glob='**/*.txt',
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    return loader.load()


def load_python_docs():
    """Carga archivos Python como documentos."""
    loader = DirectoryLoader(
        DOCS_PATH,
        glob='**/*.py',
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    return loader.load()


def load_pdf_docs():
    """Carga documentos PDF."""
    loader = DirectoryLoader(
        DOCS_PATH,
        glob='**/*.pdf',
        loader_cls=PyPDFLoader
    )
    return loader.load()


def load_all_documents():
    """
    Carga todos los documentos desde ./docs/
    Soporta: .md, .txt, .py, .pdf

    Returns:
        list: Lista de documentos cargados
    """
    docs = []

    loaders_config = [
        ("Markdown", load_markdown_docs),
        ("Texto", load_text_docs),
        ("Python", load_python_docs),
        ("PDF", load_pdf_docs),
    ]

    for format_name, loader_func in loaders_config:
        try:
            loaded = loader_func()
            if loaded:
                docs.extend(loaded)
                print(f"[OK] {format_name}: {len(loaded)} documento(s)")
        except Exception as e:
            print(f"[ERROR] {format_name}: {e}")

    return docs
