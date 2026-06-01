# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Instalar dependencias
pipenv install

# Indexar documentos (poblar ChromaDB) — correr cada vez que cambien docs/
pipenv run python indexar.py

# Iniciar el chat RAG interactivo
pipenv run python consultar.py

# Evaluar métricas del RAG (REPL interactivo)
pipenv run python evaluar.py

# Ver progreso y estadísticas de evaluaciones
pipenv run python ver_progreso.py
```

No hay tests automatizados ni linter configurado.

## Prerequisitos de runtime

Cuando `LLM_PROVIDER=ollama` o `EMBED_PROVIDER=ollama` (defaults), Ollama debe estar corriendo. `preflight()` en `src/providers/health.py` lo valida al arrancar cada entry point: hace ping, intenta auto-arrancar `ollama serve` si está caído, y valida que los modelos requeridos (`mistral:7b`, `nomic-embed-text` por defecto) estén descargados.

Para cambiar de proveedor, editar `.env` (copiar desde `.env.example`).

## Arquitectura

Entry points delgados (`consultar.py`, `indexar.py`, `evaluar.py`, `ver_progreso.py`) que delegan toda la lógica a `src/`.

### Capa de proveedores — `src/providers/`

Factory pattern: `get_llm()` y `get_embeddings()` en `__init__.py` instancian el proveedor activo según `LLM_PROVIDER` / `EMBED_PROVIDER` en `.env`. Proveedores implementados: `ollama.py`, `claude.py`, `openai_provider.py`. Para agregar un proveedor: crear el módulo con `get_llm()` / `get_embeddings()` y agregar el case en `__init__.py`.

`health.py` maneja resiliencia de Ollama: `is_ollama_up`, `ensure_ollama` (ping → auto-arranque → polling → validación de modelos), `preflight` (wrapper de alto nivel, no-op para proveedores remotos).

### Flujo de consulta — `consultar.py`

Al arrancar: `preflight()` → `load_vectorstore()` → `get_llm()`. Estos se cargan **una sola vez**; `/mode` solo cambia el template de prompt en memoria.

Por turno: `retriever.invoke(query)` → formatear prompt con `{context}` + `{history}` + `{question}` → `llm.stream()` token a token. `_chunk_text(chunk)` normaliza `str` (Ollama) vs `AIMessageChunk` (Claude/OpenAI).

Auto-reconexión: ante `ConnectionError` en retrieval o streaming, reintenta una vez tras `ensure_ollama()`.

### Historial de chats — `src/chat/store.py`

Layout en disco: `data/chats/<YYYYMMDD-HHMMSS>/{meta.json, messages.jsonl}`. `list_chats()` lee solo `meta.json`; el historial completo vive en disco. Al LLM se envían los últimos `MAX_HISTORY_TURNS` turnos como texto plano en `{history}`.

`ChatSession` es la entidad en memoria: `append(role, content)` escribe append-only al JSONL. `history_block(max_turns)` genera el bloque de texto para el prompt.

### Configuración — `src/config.py`

**Única fuente de verdad**: paths, modelos, `RAG_MODES`, parámetros RAG y métricas. Carga `.env` via `python-dotenv`. Modificar aquí; nunca hardcodear valores en otros módulos.

Para agregar un modo: agregar entrada a `RAG_MODES` con `description` y `prompt_template` (variables `{context}`, `{question}`, opcionalmente `{history}`). El modo `refine` no usa `{context}` ni `{history}`.

### Indexación — `indexar.py` + `src/rag/loader.py`

Carga `.md`, `.txt`, `.py`, `.pdf` desde `./docs/`, divide en chunks (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`), genera embeddings y persiste en ChromaDB (`./chroma_db/`). Correr de nuevo cuando cambien los documentos.

## Paquetes clave y restricciones de imports

| Paquete | Uso | Restricción |
|---|---|---|
| `langchain-ollama` | `OllamaLLM`, `OllamaEmbeddings` | **No** usar `langchain_community` (deprecado desde 0.3.1) |
| `langchain-classic` | `RetrievalQA`, `PromptTemplate` | **No** usar `langchain.chains` / `langchain.prompts` directamente |
| `langchain-chroma` | `Chroma` vectorstore | **No** usar el de `langchain_community` |
| `langchain-community` | Solo loaders (`DirectoryLoader`, `PyPDFLoader`) | — |
| `langchain-anthropic` | `ChatAnthropic` | — |
| `langchain-openai` | `ChatOpenAI`, `OpenAIEmbeddings` | — |

## Chat interactivo — comandos y keybindings

| Input | Acción |
|---|---|
| `Enter` | Envía la pregunta |
| `Alt+Enter` | Inserta salto de línea |
| `/mode <nombre>` | Cambia el modo (solo swapea prompt template) |
| `/modes` | Lista modos disponibles |
| `/new` | Crea un chat nuevo |
| `/chats` | Lista todos los chats |
| `/open <n\|id>` | Abre un chat por número o id |
| `/rename <título>` | Renombra el chat activo |
| `/delete <n\|id>` | Elimina un chat permanentemente |
| `/clear` | Limpia el historial del chat activo |
| `/history` | Muestra los turnos del chat activo |
| `/reconnect` | Fuerza reconexión con Ollama sin reiniciar |
| `/config` | Muestra configuración activa y estado de Ollama |
| `/help` | Muestra ayuda |
| `/exit` / `/salir` | Termina la sesión |

## Directorios de datos

- `./docs/` — documentos fuente (ignorados por git excepto `docs/CLAUDE.md`)
- `./chroma_db/` — vectorstore persistido (generado por `indexar.py`)
- `./data/chats/` — chats multi-sesión en JSONL
- `./data/metrics/` — evaluaciones y estadísticas
- `./data/.rag_history` — historial de inputs del REPL entre sesiones
