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

## Resiliencia de Ollama ✅ (completada)

**Archivos:**
- `src/providers/health.py` — `is_ollama_up`, `installed_models`, `missing_models`, `required_ollama_models`, `start_ollama`, `ensure_ollama`, `preflight`
- `src/config.py` — `OLLAMA_AUTOSTART` (default true), `OLLAMA_STARTUP_WAIT` (default 15s)
- `.env.example` — documentadas las dos variables nuevas

**Comportamiento al arrancar:**
1. `preflight()` hace ping a Ollama → si responde, continúa
2. Si está caído: lanza `ollama serve` detached (Windows-compatible) y hace polling ~1s hasta `OLLAMA_STARTUP_WAIT` segundos
3. Valida que los modelos requeridos estén descargados; si falta alguno, avisa con `ollama pull <modelo>`
4. Si falla todo: loop `Reintentar [r] / Salir [q]` — no crashea

**Integrado en:** `consultar.py`, `indexar.py`, `src/metrics/evaluator.py:load_qa_chain`

**A mitad de sesión:** retrieval y streaming tienen reintento automático (1 vez) tras reconexión; `/reconnect` fuerza reconexión manual sin reiniciar el proceso. `/config` muestra estado de Ollama (activo/caído) en tiempo real.

**Para Claude/OpenAI:** `preflight()` retorna `True` de inmediato — no intenta levantar nada.

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

### Fase 3 — Chats multi-sesión con historial ✅ (completada)

**Objetivo**: múltiples chats persistentes con historial de conversación, donde el LLM recuerda los turnos previos del chat activo.

**Archivos nuevos:**
- `src/utils/jsonl.py` — helper `append_jsonl` / `read_jsonl` (centraliza patrón duplicado en métricas)
- `src/chat/__init__.py` + `src/chat/store.py` — `ChatSession`, `list_chats`, `create_chat`, `load_chat`, `delete_chat`

**Layout de almacenamiento:**
```
data/chats/<id>/          # id = timestamp YYYYMMDD-HHMMSS
  meta.json               # {id, title, mode, created, updated, message_count}
  messages.jsonl          # append-only — un mensaje por línea
```

**Optimizaciones de rendimiento/espacio:**
- `list_chats()` lee solo `meta.json` — no carga mensajes
- Solo el chat activo vive en RAM
- Escritura O(1): append-only, nunca reescribe el historial
- LLM recibe solo los últimos `MAX_HISTORY_TURNS` turnos (default 4) — protege la ventana de contexto de modelos locales
- El historial completo siempre permanece en disco (nunca se pierde)

**Comandos nuevos:**

| Comando | Descripción |
|---------|-------------|
| `/new` | Crea un chat nuevo |
| `/chats` | Lista todos los chats (tabla Rich) |
| `/open <n\|id>` | Abre un chat por número o id |
| `/rename <título>` | Renombra el chat activo |
| `/delete <n\|id>` | Elimina un chat permanentemente |
| `/clear` | Limpia el historial del chat activo |
| `/history` | Muestra los turnos del chat activo |

**Variables de entorno:**
```env
MAX_HISTORY_TURNS=4   # turnos enviados al LLM por query (default 4)
```

**Auto-comportamiento:**
- Al arrancar: carga el chat más reciente (o crea uno nuevo si no hay ninguno)
- Título: se genera automáticamente desde la 1ª pregunta del usuario
- `/mode <nombre>` persiste el modo en el `meta.json` del chat activo

**Portabilidad:** el historial se inyecta como texto en el prompt (`{history}`) — funciona igual en Ollama, Claude y OpenAI sin ramificar por proveedor.

---

### Fase 4 — UX de consola ✅ (completada)

**Objetivo**: mejorar la experiencia en consola sin cambiar la arquitectura.

**Items completados:**
- [x] Fuentes al final de cada respuesta — completado en Fase 2
- [x] Arreglar `evaluar.py`: `qa_chain({"query": ...})` → `.invoke({"query": ...})`
- [x] Comando `/config` — muestra LLM provider/modelo, embed provider/modelo, retriever K, modo activo
- [x] Historial persistente entre sesiones — `prompt_toolkit.FileHistory` en `data/.rag_history`
- [x] Autocompletado con Tab — `WordCompleter` ofrece comandos y nombres de modos

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

## Mejoras futuras / deuda técnica

### Seguridad — Confinamiento de rutas en `src/chat/store.py`

**Contexto:** Un security review identificó que `chat_id` proveniente del input del usuario se une directamente a rutas de filesystem sin verificar que el resultado quede dentro de `CHATS_DIR`. Python's `pathlib` no bloquea segmentos `..` durante el join con `/`.

**Riesgo actual:** Bajo (herramienta CLI local de usuario único, sin exposición de red). Sin embargo, si en el futuro el proyecto expone la funcionalidad de chats via API o interfaz multiusuario, esto se convierte en una vulnerabilidad concreta de path traversal que podría permitir leer o eliminar directorios arbitrarios en el sistema.

**Afecta:** `src/chat/store.py` — funciones `_meta_path`, `load_chat`, `delete_chat`.

**Fix recomendado (una línea por función):**
```python
def _safe_chat_dir(chat_id: str) -> Path:
    candidate = (CHATS_DIR / chat_id).resolve()
    if not candidate.is_relative_to(CHATS_DIR.resolve()):
        raise ValueError(f"chat_id inválido: '{chat_id}'")
    return candidate
```
O alternativamente, validar el formato del `chat_id` en `_resolve_chat_ref` antes de cualquier operación de filesystem:
```python
import re
if not re.fullmatch(r'[\w-]{1,64}', chat_id):
    raise ValueError(f"chat_id inválido: '{chat_id}'")
```
Los IDs generados por `create_chat` ya usan formato `YYYYMMDD-HHMMSS`, por lo que esta regex bloquea cualquier traversal sin romper el comportamiento existente.

**Prioridad:** Baja hoy — implementar antes de cualquier exposición multiusuario o API.

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
