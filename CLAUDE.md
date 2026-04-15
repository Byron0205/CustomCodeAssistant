# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Activar el entorno virtual (pipenv)
pipenv shell

# Indexar documentos (poblar ChromaDB)
pipenv run python indexar.py

# Iniciar el chat RAG interactivo
pipenv run python consultar.py

# Instalar dependencias
pipenv install
```

Ollama debe estar corriendo localmente antes de ejecutar cualquiera de los dos scripts. Los modelos requeridos son `nomic-embed-text` (embeddings) y `qwen2.5-coder:3b` (LLM).

## Arquitectura

El proyecto es un sistema RAG (Retrieval-Augmented Generation) local con dos etapas separadas:

### 1. Indexación (`indexar.py`)
Carga documentos desde `./docs/` (`.md`, `.txt`, `.py`), los divide en chunks de 800 tokens con solapamiento de 100, genera embeddings con `nomic-embed-text` vía Ollama y los persiste en ChromaDB (`./chroma_db/`). Hay que correr este script cada vez que se agreguen o modifiquen documentos en `./docs/`.

### 2. Consulta (`consultar.py`)
Carga el vectorstore desde `./chroma_db/`, construye una cadena `RetrievalQA` con `qwen2.5-coder:3b` como LLM y expone un REPL interactivo. Recupera los 5 chunks más relevantes (`k=5`) por consulta y muestra las fuentes usadas en cada respuesta.

### Paquetes clave
- `langchain-ollama` — `OllamaEmbeddings` y `OllamaLLM`. **No usar** las versiones de `langchain_community` (deprecadas desde 0.3.1)
- `langchain-community` — loaders (`DirectoryLoader`, `PyPDFLoader`), vectorstore (`Chroma`)
- `langchain-classic` — chains y prompts de la API clásica (`RetrievalQA`, `PromptTemplate`). **No usar `langchain.chains` ni `langchain.prompts`** directamente; en LangChain v1.x esos módulos fueron movidos a `langchain-classic`.
- `langchain-text-splitters` — `RecursiveCharacterTextSplitter`
- `chromadb` — base de datos vectorial local

### Directorios de datos
- `./docs/` — documentos fuente a indexar (ignorados por git excepto `docs/CLAUDE.md`)
- `./chroma_db/` — base de datos vectorial persistida (generada por `indexar.py`)
