"""
Configuración centralizada del proyecto RAG.
ÚNICA fuente de verdad para paths, modelos y parámetros.
"""

from pathlib import Path

# Rutas
DOCS_PATH = "./docs"
CHROMA_PATH = "./chroma_db"
DATA_DIR = Path("./data")
METRICS_DIR = DATA_DIR / "metrics"

# Crear directorio de métricas si no existe
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# Archivos de métricas
EVALUATIONS_FILE = METRICS_DIR / "evaluations.jsonl"
STATS_FILE = METRICS_DIR / "stats.json"

# Modelos Ollama
EMBED_MODEL = "nomic-embed-text"
#LLM_MODEL = "qwen2.5-coder:3b"
LLM_MODEL = "mistral:7b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Parámetros RAG
RETRIEVER_K = 5
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Prompt base para RAG
RAG_PROMPT_TEMPLATE = """
Eres un asistente de programacion. Usa el siguiente contexto
extraido de los documentos del usuario para responder su pregunta.
Si no encuentras la respuesta en el contexto, dilo claramente.
Responde en espanol salvo que el codigo lo requiera en ingles.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

RAG_MODES = {
    "default": {
        "description": "Asistente de programación general",
        "prompt_template": RAG_PROMPT_TEMPLATE,
    },
    "jira": {
        "description": "Redacción y planeación de tareas Jira",
        "prompt_template": """Eres un experto en planeación ágil y redacción de tareas Jira.
Usa el contexto para generar o mejorar tareas con esta estructura obligatoria:
- **Summary** (título conciso, máx. 80 chars)
- **Flujo de trabajo** (orden de eventos para correcto funcionamiento si aplica)
- **Descripción** (qué se hace y por qué)
- **Criterios de aceptación** (checklist verificable)
- **Story Points** (estimación: 1, 2, 3, 5 u 8)
- **Subtareas** (si aplica)
Responde en español.

Contexto:
{context}

Pregunta: {question}

Respuesta:""",
    },
    "code": {
        "description": "Análisis y depuración de código",
        "prompt_template": """Eres un revisor de código senior. Analiza el código y SIEMPRE reporta en este orden:
1. Errores de sintaxis y bugs potenciales
2. Antipatrones (ej: `;` innecesarios en Python, mutaciones implícitas, variables no usadas)
3. Violaciones de estilo (PEP8 para Python, convenciones ESLint para JS)
4. Sugerencias de mejora de rendimiento y legibilidad
Si el código no tiene problemas, indícalo explícitamente.
Responde en español; conserva el código en su lenguaje original.

Contexto:
{context}

Pregunta: {question}

Respuesta:""",
    },
}

DEFAULT_MODE = "default"
