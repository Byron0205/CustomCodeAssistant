"""
Configuración centralizada del proyecto RAG.
ÚNICA fuente de verdad para paths, modelos y parámetros.
Lee variables de entorno desde .env (via python-dotenv).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Rutas
DOCS_PATH = "./docs"
CHROMA_PATH = "./chroma_db"
DATA_DIR = Path("./data")
METRICS_DIR = DATA_DIR / "metrics"

METRICS_DIR.mkdir(parents=True, exist_ok=True)

EVALUATIONS_FILE = METRICS_DIR / "evaluations.jsonl"
STATS_FILE = METRICS_DIR / "stats.json"

CHATS_DIR = DATA_DIR / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)

# Proveedores
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama")

# Modelos por defecto según proveedor
_LLM_MODEL_DEFAULTS = {
    "ollama": "mistral:7b",
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}
_EMBED_MODEL_DEFAULTS = {
    "ollama": "nomic-embed-text",
    "openai": "text-embedding-3-small",
}

LLM_MODEL = os.getenv("LLM_MODEL", _LLM_MODEL_DEFAULTS.get(LLM_PROVIDER, "mistral:7b"))
EMBED_MODEL = os.getenv("EMBED_MODEL", _EMBED_MODEL_DEFAULTS.get(EMBED_PROVIDER, "nomic-embed-text"))

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_AUTOSTART = os.getenv("OLLAMA_AUTOSTART", "true").lower() == "true"
OLLAMA_STARTUP_WAIT = int(os.getenv("OLLAMA_STARTUP_WAIT", "15"))

# API keys (None si no están definidas)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Parámetros RAG
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Ventana de historial conversacional enviada al LLM por turno
# N turnos = N pares usuario/asistente. El historial completo sigue en disco.
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "4"))

# Prompt base para RAG
RAG_PROMPT_TEMPLATE = """
Eres un asistente de programacion. Usa el siguiente contexto
extraido de los documentos del usuario para responder su pregunta.
Si no encuentras la respuesta en el contexto, dilo claramente.
Responde en espanol salvo que el codigo lo requiera en ingles.

Contexto:
{context}

{history}Pregunta: {question}

Respuesta:"""

RAG_MODES = {
    "default": {
        "description": "Asistente de programación general",
        "prompt_template": RAG_PROMPT_TEMPLATE,
    },
    "jira": {
        "description": "Redacción y planeación de tareas Jira",
        "prompt_template": """Eres un experto en planeación ágil y redacción de tareas Jira con enfoque en precisión técnica.

        Tu objetivo es generar requerimientos claros, específicos y verificables.
        NO generes respuestas genéricas.

        Reglas obligatorias:
        - NO usar palabras ambiguas: "debería", "podría", "recomendado"
        - SIEMPRE especificar datos concretos (ej: métricas, campos, acciones)
        - SIEMPRE definir comportamiento del sistema
        - SIEMPRE incluir interacción del usuario cuando aplique
        - SIEMPRE incluir estados: loading, error, empty (si aplica)

        Estructura obligatoria:

        - **Summary** (máx. 80 chars, específico)
        - **Flujo de trabajo** (paso a paso si aplica)
        - **Descripción** (qué hace + para qué sirve)
        - **Componentes de interfaz** (si aplica UI)
        - **Reglas de interacción** (eventos y comportamiento)
        - **Criterios de aceptación** (checklist verificable)
        - **Story Points** (estimación: 1, 2, 3, 5 u 8)
        - **Subtareas** (si aplica)

        Responde en español.

        Contexto:
        {context}

        {history}Pregunta: {question}

        Respuesta:""",
    },
    "refine": {
        "description": "Sanitización y refinamiento de prompts",
        "prompt_template": """Eres un experto en ingeniería de prompts. Recibes un prompt en bruto del usuario y debes devolver una versión refinada.

Reglas obligatorias:
- Elimina muletillas y rellenos ("básicamente", "como tal", "o sea", "tipo", "este", "pues", etc.)
- Elimina contexto redundante o irrelevante para la tarea
- Conserva la intención original y los detalles técnicos específicos (nombres, métricas, tecnologías, restricciones)
- Reescribe en imperativo y voz activa cuando aporte claridad
- No inventes requisitos que el usuario no mencionó
- Si el prompt ya está bien, dilo explícitamente y devuélvelo sin cambios

Estructura obligatoria de respuesta:

**Prompt refinado:**
<el prompt limpio, listo para copiar>

**Cambios aplicados:**
- <cambio 1: qué se eliminó o ajustó y por qué>
- <cambio 2: ...>

Responde en español.

Pregunta: {question}

Respuesta:""",
    },
}

DEFAULT_MODE = "default"
