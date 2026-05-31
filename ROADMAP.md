# RAG Project — Roadmap y Documentación Técnica

## Visión

Sistema RAG (Retrieval-Augmented Generation) local y portable que funciona en consola y puede conectarse a cualquier proveedor de LLM — local (Ollama) o en la nube (Claude, OpenAI) — sin cambiar el código, solo con variables de entorno.

---

## Arquitectura actual

```
consultar.py / indexar.py / evaluar.py / ver_progreso.py
        │  (entry points delgados, sin lógica)
        ▼
    src/
    ├── config.py              ← ÚNICA fuente de verdad (paths, modelos, modos)
    ├── providers/             ← [FASE 1] abstracción de proveedores LLM/embeddings
    │   ├── __init__.py        ← factory: get_llm() y get_embeddings()
    │   ├── base.py            ← Protocol de interfaz
    │   ├── ollama.py          ← Ollama local
    │   ├── claude.py          ← Anthropic Claude API
    │   └── openai_provider.py ← OpenAI API
    ├── rag/
    │   ├── chain.py           ← build_chain(mode) → RetrievalQA
    │   └── loader.py          ← carga docs de ./docs/
    ├── metrics/
    │   ├── evaluator.py       ← mide latencia, calidad, relevancia
    │   └── progress.py        ← reportes de evaluaciones
    └── utils/
        ├── spinner.py         ← spinner con contador de tiempo
        └── markdown_formatter.py ← Rich markdown + tablas
```

### Flujo de datos

```
indexar.py → loader.py → splitter → get_embeddings() → ChromaDB
consultar.py → build_chain(mode) → get_llm() + ChromaDB → RetrievalQA → respuesta
```

---

## Compatibilidad de proveedores

| Proveedor    | LLM | Embeddings | API Key requerida    | Notas                                   |
|--------------|-----|------------|----------------------|-----------------------------------------|
| `ollama`     | ✓   | ✓          | No (local)           | Requiere Ollama corriendo localmente    |
| `claude`     | ✓   | ✗          | `ANTHROPIC_API_KEY`  | Sin embeddings nativos; usar EMBED_PROVIDER=ollama u openai |
| `openai`     | ✓   | ✓          | `OPENAI_API_KEY`     | Embeddings: text-embedding-3-small      |

### Modelos por defecto

| Proveedor | LLM default         | Embed default           |
|-----------|---------------------|-------------------------|
| ollama    | `mistral:7b`        | `nomic-embed-text`      |
| claude    | `claude-sonnet-4-6` | N/A                     |
| openai    | `gpt-4o-mini`       | `text-embedding-3-small`|

---

## Roadmap

### Fase 1 — Abstracción de proveedores ✅ (completada)

**Objetivo**: desacoplar el código del vendor de LLM/embeddings para poder cambiar entre Ollama, Claude y OpenAI con solo cambiar variables de entorno.

**Cambios realizados:**
- Creado `src/providers/` con interfaz unificada (Protocol)
- Proveedores implementados: `ollama`, `claude`, `openai`
- `.env` para configuración sensible (API keys, proveedor activo)
- `src/config.py` usa `python-dotenv`; carga `.env` automáticamente
- `src/rag/chain.py` e `indexar.py` usan `get_llm()` / `get_embeddings()` del factory
- Defaults por proveedor (modelo LLM y embed)

**Variables de entorno clave:**
```env
LLM_PROVIDER=ollama          # ollama | claude | openai
EMBED_PROVIDER=ollama        # ollama | openai  (Claude no tiene embeddings)
LLM_MODEL=mistral:7b         # override del modelo LLM (opcional)
EMBED_MODEL=nomic-embed-text # override del modelo de embeddings (opcional)
ANTHROPIC_API_KEY=sk-ant-... # requerida si LLM_PROVIDER=claude
OPENAI_API_KEY=sk-...        # requerida si LLM_PROVIDER=openai o EMBED_PROVIDER=openai
OLLAMA_BASE_URL=http://localhost:11434
```

**Agregar un nuevo proveedor futuro:**
1. Crear `src/providers/<nombre>.py` con `get_llm()` y/o `get_embeddings()`
2. Agregar el case en `src/providers/__init__.py`
3. Documentar en esta tabla de compatibilidad

---

### Fase 2 — Streaming de respuestas ✅ (completada)

**Objetivo**: mostrar la respuesta del LLM en tiempo real en lugar de esperar la respuesta completa.

**Cambios realizados:**
- `src/rag/chain.py`: nuevo `load_vectorstore()` — carga el vectorstore sin construir el chain completo
- `consultar.py`: refactor completo del loop principal
  - Vectorstore + LLM se cargan **una sola vez** al startup (antes se reconstruían en cada query y en cada `/mode`)
  - Por cada query: retrieve docs → formatear prompt → `llm.stream()` token a token
  - Indicador `[>>] Recuperando contexto...` durante retrieval; `[>>] Generando...` hasta el primer token
  - **Fuentes mostradas** al final de cada respuesta (bonus de Fase 4)
  - **Latencia mostrada** en segundos al final de cada respuesta
  - `/mode` ya no reconstruye nada — solo cambia el template de prompt en memoria
- `_chunk_text(chunk)`: helper que normaliza el output de streaming entre providers
  - Ollama (`OllamaLLM`) → yields `str`
  - Claude / OpenAI → yields `AIMessageChunk` con `.content`
- `build_chain()` se mantiene intacto para backward compat con `evaluar.py`

**UX resultante:**
```
──────────────────────────────────────────────────────────────
[default] >> dame un ejemplo de clean code

[Respuesta]
El principio más importante del Clean Code es...   ← tokens aparecen uno a uno

Fuentes: clean-code.md, best-practices.md | 4.2s
──────────────────────────────────────────────────────────────
```

---

### Fase 3 — Historial de conversación ⬜ (pendiente)

**Objetivo**: mantener contexto entre preguntas dentro de la sesión.

**Qué cambiar:**
- Agregar `ConversationBufferMemory` o `ConversationSummaryMemory` a `chain.py`
- Nuevo comando `/clear` para resetear el contexto
- Nuevo comando `/history` para ver el historial de la sesión actual
- Decidir cuántos turnos guardar (parámetro `MAX_HISTORY_TURNS` en config)

**Consideración**: con historial activado el prompt crece — importante para modelos con ventana de contexto chica (ej: mistral:7b local). `ConversationSummaryMemory` comprime automáticamente, pero requiere un LLM call extra.

---

### Fase 4 — UX de consola ⬜ (pendiente)

**Objetivo**: mejorar la experiencia en consola sin cambiar la arquitectura.

**Items:**
- [ ] Mostrar fuentes al final de cada respuesta en `consultar.py` (la chain ya las devuelve, solo falta imprimirlas)
- [ ] Arreglar `evaluar.py`: usa `qa_chain({"query": ...})` (API vieja) en lugar de `.invoke()`
- [ ] Comando `/config` para ver proveedor y modelo activos sin salir
- [ ] Historial de comandos persistent entre sesiones (via `prompt_toolkit` `FileHistory`)
- [ ] Autocompletado de comandos `/` con `prompt_toolkit` `WordCompleter`

---

## Configuración rápida

### Setup inicial
```bash
pipenv install
cp .env.example .env
# editar .env con el proveedor y keys deseadas
pipenv run python indexar.py    # indexar docs (una sola vez)
pipenv run python consultar.py  # iniciar chat
```

### Cambiar de Ollama a Claude
```env
# .env
LLM_PROVIDER=claude
EMBED_PROVIDER=ollama           # Claude no tiene embeddings
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-6    # opcional, es el default
```

### Cambiar a OpenAI full
```env
# .env
LLM_PROVIDER=openai
EMBED_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Comandos del chat interactivo

| Comando           | Acción                                      |
|-------------------|---------------------------------------------|
| `Enter`           | Envía la pregunta                           |
| `Alt+Enter`       | Inserta salto de línea                      |
| `/mode <nombre>`  | Cambia el modo del asistente                |
| `/modes`          | Lista modos disponibles                     |
| `/help`           | Muestra ayuda                               |
| `/exit`           | Termina la sesión                           |

## Modos disponibles

| Modo      | Descripción                              |
|-----------|------------------------------------------|
| `default` | Asistente de programación general        |
| `jira`    | Redacción y planeación de tareas Jira    |
| `refine`  | Sanitización y refinamiento de prompts   |

Para agregar un nuevo modo: editar `RAG_MODES` en `src/config.py` — no hay más cambios necesarios.

---

## Paquetes clave

| Paquete                | Uso                                      | Restricciones                              |
|------------------------|------------------------------------------|--------------------------------------------|
| `langchain-ollama`     | `OllamaEmbeddings`, `OllamaLLM`          | No usar versiones de `langchain_community` |
| `langchain-anthropic`  | `ChatAnthropic`                          | Requiere `ANTHROPIC_API_KEY`               |
| `langchain-openai`     | `ChatOpenAI`, `OpenAIEmbeddings`         | Requiere `OPENAI_API_KEY`                  |
| `langchain-classic`    | `RetrievalQA`, `PromptTemplate`          | No usar `langchain.chains` directo         |
| `langchain-chroma`     | `Chroma` vectorstore                     | No usar el de `langchain_community`        |
| `langchain-community`  | Loaders únicamente                       | Solo para `DirectoryLoader`, `PyPDFLoader` |
| `python-dotenv`        | Carga `.env` en `config.py`             | —                                          |
