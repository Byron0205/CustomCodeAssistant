import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

#config
DOCS_PATH = './docs'
CHROMA_PATH = './chroma_db'
EMBED_MODEL = 'nomic-embed-text'

def indexar():
    #1. cargar documentos
    loaders = [
        DirectoryLoader(DOCS_PATH,glob='**/*.md', loader_cls=TextLoader),
        DirectoryLoader(DOCS_PATH,glob='**/*.txt', loader_cls=TextLoader),
        DirectoryLoader(DOCS_PATH,glob='**/*.py', loader_cls=TextLoader)
    ]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    print(f'documentos cargados: {len(docs)}')

    #2 dividir documentos
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=['\n\n', '\n', ' ', '']
    )
    chunks = splitter.split_documents(docs)
    print(f'chunks generados: {len(chunks)}')

    #3. Crear embeddings y guardar en ChromaDB
    embeddings= OllamaEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f'Indexacion completa. Base de datos guardada en: {CHROMA_PATH}')

if __name__ == "__main__":
    indexar()