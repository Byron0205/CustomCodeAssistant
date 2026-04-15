#!/usr/bin/env python3
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
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import statistics

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate


# Configuración
CHROMA_DB_PATH = "./chroma_db/"
METRICS_DIR = Path("./metrics/")
EVALUATIONS_FILE = METRICS_DIR / "evaluations.jsonl"
STATS_FILE = METRICS_DIR / "stats.json"

# Crear directorio de métricas si no existe
METRICS_DIR.mkdir(exist_ok=True)

# Preguntas de evaluación predefinidas
EVAL_QUESTIONS = [
    "¿Cuál es el propósito principal del proyecto?",
    "¿Qué modelos de Ollama se requieren?",
    "¿Cuál es el tamaño de los chunks de indexación?",
    "¿Qué directorios contiene la estructura del proyecto?",
    "¿Cuántos chunks se recuperan en cada consulta?",
]


def load_qa_chain():
    """Carga la cadena de RAG."""
    try:
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )

        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )

        llm = OllamaLLM(
            model="qwen2.5-coder:3b",
            base_url="http://localhost:11434"
        )

        # Prompt customizado para RAG
        prompt_template = """
Usa la siguiente información para responder la pregunta.
Si la información no es suficiente, di que no tienes datos suficientes.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        return qa_chain
    except Exception as e:
        print(f"❌ Error al cargar el RAG: {e}")
        print("⚠️  ¿Ollama está corriendo? ¿ChromaDB fue indexado?")
        sys.exit(1)


def evaluate_question(qa_chain, question: str) -> dict:
    """
    Evalúa una pregunta con métricas.
    Retorna: tiempo, respuesta, fuentes, etc.
    """
    start_time = time.time()

    try:
        result = qa_chain({"query": question})
        end_time = time.time()

        elapsed_time = end_time - start_time
        response = result.get("result", "")
        sources = result.get("source_documents", [])

        # Extraer nombres de archivos fuente
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
            "quality_score": None,  # Se llena manualmente
            "relevance_score": None,  # Se llena manualmente
            "notes": None  # Se llena manualmente
        }

        return evaluation
    except Exception as e:
        print(f"❌ Error evaluando pregunta: {e}")
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
                print("⚠️  Score debe estar entre 1-5")
                evaluation["quality_score"] = None

        relevance = input("Relevancia (1-5, o Enter para omitir): ").strip()
        if relevance:
            evaluation["relevance_score"] = int(relevance)
            if not (1 <= evaluation["relevance_score"] <= 5):
                print("⚠️  Score debe estar entre 1-5")
                evaluation["relevance_score"] = None

        notes = input("Notas (Enter para omitir): ").strip()
        if notes:
            evaluation["notes"] = notes

        return True
    except ValueError:
        print("❌ Entrada inválida")
        return False


def print_statistics(stats: dict):
    """Imprime estadísticas formateadas."""
    if not stats:
        print("No hay estadísticas disponibles aún.")
        return

    print("\n📊 ESTADÍSTICAS DEL RAG")
    print("="*70)

    print(f"\n📈 Total de evaluaciones: {stats['total_evaluations']}")

    if stats.get('date_range'):
        print(f"📅 Rango: {stats['date_range']['first'][:10]} a {stats['date_range']['last'][:10]}")

    print("\n⏱️  LATENCIA")
    print(f"  Promedio: {stats['latency']['avg_seconds']}s")
    print(f"  Mínimo: {stats['latency']['min_seconds']}s")
    print(f"  Máximo: {stats['latency']['max_seconds']}s")

    print("\n⭐ CALIDAD")
    if stats['quality']['avg_score']:
        print(f"  Promedio: {stats['quality']['avg_score']}/5 ({stats['quality']['evaluations_with_score']} evaluadas)")
    else:
        print("  Sin evaluaciones de calidad aún")

    print("\n📍 RELEVANCIA")
    if stats['relevance']['avg_score']:
        print(f"  Promedio: {stats['relevance']['avg_score']}/5 ({stats['relevance']['evaluations_with_score']} evaluadas)")
    else:
        print("  Sin evaluaciones de relevancia aún")

    print("\n📚 COBERTURA")
    print(f"  Promedio de fuentes por respuesta: {stats['avg_sources_per_response']}")
    print(f"  Promedio de chunks por respuesta: {stats['avg_chunks_per_response']}")

    print("\n" + "="*70)


def main():
    """Flujo principal de evaluación."""
    print("🔍 EVALUADOR DE MÉTRICAS DEL RAG")
    print("="*70)

    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Evaluar preguntas predefinidas")
        print("2. Hacer una pregunta personalizada")
        print("3. Ver estadísticas")
        print("4. Salir")

        choice = input("\nOpción (1-4): ").strip()

        if choice == "1":
            print("\n📋 Evaluando preguntas predefinidas...\n")
            qa_chain = load_qa_chain()

            for i, question in enumerate(EVAL_QUESTIONS, 1):
                print(f"[{i}/{len(EVAL_QUESTIONS)}] {question}")
                evaluation = evaluate_question(qa_chain, question)

                if evaluation:
                    if rate_evaluation(evaluation):
                        save_evaluation(evaluation)
                        print("✅ Evaluación guardada")
                    else:
                        print("⏭️  Salteada")
                else:
                    print("❌ Error en la evaluación")

        elif choice == "2":
            print("\n❓ Pregunta personalizada")
            question = input("Pregunta: ").strip()

            if question:
                qa_chain = load_qa_chain()
                print("\n⏳ Evaluando...")
                evaluation = evaluate_question(qa_chain, question)

                if evaluation:
                    if rate_evaluation(evaluation):
                        save_evaluation(evaluation)
                        print("✅ Evaluación guardada")
                else:
                    print("❌ Error en la evaluación")

        elif choice == "3":
            evaluations = load_evaluations()
            stats = calculate_statistics(evaluations)
            print_statistics(stats)

            # Guardar stats
            with open(STATS_FILE, "w") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Stats guardadas en {STATS_FILE}")

        elif choice == "4":
            print("\n👋 Hasta luego")
            break

        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    main()
