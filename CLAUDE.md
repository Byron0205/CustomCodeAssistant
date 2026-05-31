# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Activar el entorno virtual (pipenv)
pipenv shell

# Indexar documentos (poblar ChromaDB) — correr cada vez que cambien docs/
pipenv run python indexar.py

# Iniciar el chat RAG interactivo
pipenv run python consultar.py

# Evaluar métricas del RAG (REPL interactivo)
pipenv run python evaluar.py

# Ver progreso y estadísticas de evaluaciones
pipenv run python ver_progreso.py

# Instalar dependencias
pipenv install
```

Ollama debe estar corriendo localmente antes de ejecutar cualquiera de los scripts. Los modelos requeridos son `nomic-embed-text` (embeddings) y `mistral:7b` (LLM, configurable en `src/config.py`).

## Arquitectura

El proyecto es un sistema RAG (Retrieval-Augmented Generation) local. Los entry points (`consultar.py`, `indexar.py`, `evaluar.py`, `ver_progreso.py`) son wrappers delgados que delegan toda la lógica a `src/`.

### Flujo de datos

**Indexación** (`indexar.py` → `src/rag/loader.py`): carga `.md`, `.txt`, `.py`, `.pdf` desde `./docs/`, divide en chunks de 800 tokens (solapamiento 100), genera embeddings con `nomic-embed-text` y persiste en ChromaDB (`./chroma_db/`).

**Consulta** (`consultar.py` → `src/rag/chain.py`): carga el vectorstore, construye una `RetrievalQA` chain con el LLM y el prompt del modo activo, recupera 5 chunks por consulta (`RETRIEVER_K`).

### Selector de modos

`consultar.py` mantiene un `current_mode` en memoria. Al cambiar con `/mode <nombre>`, llama `build_chain(mode)` que reconstruye solo la chain (sin recargar embeddings ni vectorstore).

Los modos están definidos en `src/config.py` como `RAG_MODES` (dict). Cada modo tiene `description` y `prompt_template` con variables `{context}` y `{question}`. Para agregar un modo nuevo, solo se agrega una entrada al dict — no hay más cambios necesarios.

Modos actuales: `default` (programación general), `jira` (redacción de tareas), `refine` (sanitización y refinamiento de prompts).

### Fuente de verdad de configuración

`src/config.py` es la única fuente de verdad: rutas, modelos (`LLM_MODEL`, `EMBED_MODEL`), parámetros RAG (`RETRIEVER_K`, `CHUNK_SIZE`, `CHUNK_OVERLAP`), prompts (`RAG_MODES`, `RAG_PROMPT_TEMPLATE`), y paths de métricas (`EVALUATIONS_FILE`, `STATS_FILE`).

### Métricas

`evaluar.py` invoca el RAG sobre preguntas predefinidas o personalizadas, pide al usuario calificar calidad y relevancia (1-5), y guarda los resultados en `./data/metrics/evaluations.jsonl`. `ver_progreso.py` lee ese archivo y genera reportes (latencia, cobertura, tendencia de calidad).

## Paquetes clave y restricciones

- `langchain-ollama` — `OllamaEmbeddings` y `OllamaLLM`. **No usar** las versiones de `langchain_community` (deprecadas desde 0.3.1).
- `langchain-classic` — `RetrievalQA` y `PromptTemplate`. **No usar** `langchain.chains` ni `langchain.prompts` directamente; esos módulos fueron movidos a `langchain-classic`.
- `langchain-chroma` — `Chroma` vectorstore (no el de `langchain_community`).
- `langchain-community` — solo para loaders (`DirectoryLoader`, `PyPDFLoader`).

## Chat interactivo — comandos y keybindings

Dentro de `consultar.py`:

| Input | Acción |
|-------|--------|
| `Enter` | Envía la pregunta |
| `Alt+Enter` | Inserta salto de línea (permite pegar bloques de código) |
| `/mode <nombre>` | Cambia el modo del asistente y reconstruye el chain |
| `/modes` | Lista modos disponibles con descripción |
| `/help` | Muestra ayuda de comandos |
| `/salir` | Termina la sesión |

## Directorios de datos

- `./docs/` — documentos fuente a indexar (ignorados por git excepto `docs/CLAUDE.md`)
- `./chroma_db/` — base de datos vectorial persistida (generada por `indexar.py`)
- `./data/metrics/` — evaluaciones en JSONL y estadísticas en JSON (generados)
