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
LLM_MODEL = "qwen2.5-coder:3b"
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
