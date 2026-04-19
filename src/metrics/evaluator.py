"""
Sistema de evaluación de métricas para el RAG.
Permite medir y trackear:
- Relevancia de respuestas
- Latencia del sistema
- Cobertura de documentos
- Calidad general
"""

import json
import time
from datetime import datetime
from pathlib import Path
import statistics

from src.config import EVALUATIONS_FILE, STATS_FILE
from src.rag.chain import build_chain
from src.utils.spinner import Spinner


EVAL_QUESTIONS = [
    "¿Cuál es el propósito principal del proyecto?",
    "¿Qué modelos de Ollama se requieren?",
    "¿Cuál es el tamaño de los chunks de indexación?",
    "¿Qué directorios contiene la estructura del proyecto?",
    "¿Cuántos chunks se recuperan en cada consulta?",
]


def load_qa_chain():
    """Carga la cadena de RAG."""
    spinner = Spinner("Cargando RAG")
    spinner.start()

    try:
        qa_chain = build_chain()
        spinner.stop()
        return qa_chain
    except Exception:
        spinner.stop()
        raise


def evaluate_question(qa_chain, question: str) -> dict:
    """
    Evalúa una pregunta con métricas.
    Retorna: tiempo, respuesta, fuentes, etc.
    """
    spinner = Spinner("Evaluando")
    spinner.start()
    start_time = time.time()

    try:
        result = qa_chain({"query": question})
        end_time = time.time()

        spinner.stop()

        elapsed_time = end_time - start_time
        response = result.get("result", "")
        sources = result.get("source_documents", [])

        source_files = list(set([
            Path(doc.metadata.get("source", "unknown")).name
            for doc in sources
        ]))

        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
            "sources": source_files,
            "num_sources": len(source_files),
            "latency_seconds": round(elapsed_time, 3),
            "chunks_retrieved": len(sources),
            "quality_score": None,
            "relevance_score": None,
            "notes": None
        }

        return evaluation
    except Exception as e:
        spinner.stop()
        print(f"[ERROR] Error evaluando pregunta: {e}")
        return None


def save_evaluation(evaluation: dict):
    """Guarda una evaluación en el archivo JSONL."""
    with open(EVALUATIONS_FILE, "a") as f:
        f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")


def load_evaluations() -> list:
    """Carga todas las evaluaciones previas."""
    if not EVALUATIONS_FILE.exists():
        return []

    evaluations = []
    with open(EVALUATIONS_FILE, "r") as f:
        for line in f:
            if line.strip():
                evaluations.append(json.loads(line))
    return evaluations


def calculate_statistics(evaluations: list) -> dict:
    """Calcula estadísticas de las evaluaciones."""
    if not evaluations:
        return {}

    latencies = [e["latency_seconds"] for e in evaluations]
    quality_scores = [e["quality_score"] for e in evaluations if e["quality_score"]]
    relevance_scores = [e["relevance_score"] for e in evaluations if e["relevance_score"]]

    stats = {
        "total_evaluations": len(evaluations),
        "date_range": {
            "first": evaluations[0]["timestamp"],
            "last": evaluations[-1]["timestamp"]
        },
        "latency": {
            "avg_seconds": round(statistics.mean(latencies), 3) if latencies else 0,
            "min_seconds": round(min(latencies), 3) if latencies else 0,
            "max_seconds": round(max(latencies), 3) if latencies else 0,
        },
        "quality": {
            "avg_score": round(statistics.mean(quality_scores), 2) if quality_scores else None,
            "evaluations_with_score": len(quality_scores)
        },
        "relevance": {
            "avg_score": round(statistics.mean(relevance_scores), 2) if relevance_scores else None,
            "evaluations_with_score": len(relevance_scores)
        },
        "avg_sources_per_response": round(
            statistics.mean([e["num_sources"] for e in evaluations]), 2
        ),
        "avg_chunks_per_response": round(
            statistics.mean([e["chunks_retrieved"] for e in evaluations]), 2
        )
    }

    return stats


def rate_evaluation(evaluation: dict):
    """Permite al usuario calificar una evaluación."""
    print("\n" + "="*70)
    print(f"Pregunta: {evaluation['question']}")
    print("-"*70)
    print(f"Respuesta: {evaluation['response'][:300]}...")
    print(f"Fuentes: {', '.join(evaluation['sources'])}")
    print(f"Latencia: {evaluation['latency_seconds']}s")
    print("="*70)

    try:
        quality = input("Calidad de respuesta (1-5, o Enter para omitir): ").strip()
        if quality:
            evaluation["quality_score"] = int(quality)
            if not (1 <= evaluation["quality_score"] <= 5):
                print("[!] Score debe estar entre 1-5")
                evaluation["quality_score"] = None

        relevance = input("Relevancia (1-5, o Enter para omitir): ").strip()
        if relevance:
            evaluation["relevance_score"] = int(relevance)
            if not (1 <= evaluation["relevance_score"] <= 5):
                print("[!] Score debe estar entre 1-5")
                evaluation["relevance_score"] = None

        notes = input("Notas (Enter para omitir): ").strip()
        if notes:
            evaluation["notes"] = notes

        return True
    except ValueError:
        print("[ERROR] Entrada inválida")
        return False


def print_statistics(stats: dict):
    """Imprime estadísticas formateadas."""
    if not stats:
        print("No hay estadísticas disponibles aún.")
        return

    print("\n[>>] ESTADÍSTICAS DEL RAG")
    print("="*70)

    print(f"\n[Evaluaciones] Total: {stats['total_evaluations']}")

    if stats.get('date_range'):
        print(f"[Período] {stats['date_range']['first'][:10]} a {stats['date_range']['last'][:10]}")

    print("\n[LATENCIA]")
    print(f"  Promedio: {stats['latency']['avg_seconds']}s")
    print(f"  Mínimo: {stats['latency']['min_seconds']}s")
    print(f"  Máximo: {stats['latency']['max_seconds']}s")

    print("\n[CALIDAD]")
    if stats['quality']['avg_score']:
        print(f"  Promedio: {stats['quality']['avg_score']}/5 ({stats['quality']['evaluations_with_score']} evaluadas)")
    else:
        print("  Sin evaluaciones de calidad aún")

    print("\n[RELEVANCIA]")
    if stats['relevance']['avg_score']:
        print(f"  Promedio: {stats['relevance']['avg_score']}/5 ({stats['relevance']['evaluations_with_score']} evaluadas)")
    else:
        print("  Sin evaluaciones de relevancia aún")

    print("\n[COBERTURA]")
    print(f"  Promedio de fuentes por respuesta: {stats['avg_sources_per_response']}")
    print(f"  Promedio de chunks por respuesta: {stats['avg_chunks_per_response']}")

    print("\n" + "="*70)
