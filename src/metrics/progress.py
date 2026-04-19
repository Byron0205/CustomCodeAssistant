"""
Visualiza el progreso y evolución de las métricas del RAG.
Muestra historial, gráficos de tendencia y comparativas.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import statistics

from src.config import EVALUATIONS_FILE, STATS_FILE


def load_evaluations() -> list:
    """Carga todas las evaluaciones."""
    if not EVALUATIONS_FILE.exists():
        return []

    evaluations = []
    with open(EVALUATIONS_FILE, "r") as f:
        for line in f:
            if line.strip():
                evaluations.append(json.loads(line))
    return evaluations


def print_header(title: str, char: str = "="):
    """Imprime un encabezado formateado."""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}")


def print_latest_evaluations(evaluations: list, limit: int = 5):
    """Muestra las últimas evaluaciones."""
    print_header("ÚLTIMAS EVALUACIONES", "-")

    recent = evaluations[-limit:] if evaluations else []

    if not recent:
        print("No hay evaluaciones registradas aún.")
        return

    for i, eval in enumerate(recent, 1):
        date = eval["timestamp"][:10]
        time = eval["timestamp"][11:19]
        q_short = eval["question"][:40] + "..." if len(eval["question"]) > 40 else eval["question"]

        print(f"\n[{i}] {date} {time}")
        print(f"    [?] {q_short}")
        print(f"    [{eval['latency_seconds']}s] {eval['chunks_retrieved']} chunks | {eval['num_sources']} fuentes")

        if eval.get("quality_score"):
            print(f"    [Calidad] {eval['quality_score']}/5", end="")
        if eval.get("relevance_score"):
            print(f" | [Relevancia] {eval['relevance_score']}/5", end="")
        if eval.get("quality_score") or eval.get("relevance_score"):
            print()


def print_quality_trend(evaluations: list):
    """Muestra la tendencia de calidad a lo largo del tiempo."""
    print_header("TENDENCIA DE CALIDAD", "-")

    rated_evals = [e for e in evaluations if e.get("quality_score") or e.get("relevance_score")]

    if len(rated_evals) < 2:
        print("Necesitas al menos 2 evaluaciones calificadas para ver tendencias.")
        return

    weeks = {}
    for eval in rated_evals:
        date_obj = datetime.fromisoformat(eval["timestamp"])
        week_start = date_obj - timedelta(days=date_obj.weekday())
        week_key = week_start.strftime("%Y-%W")

        if week_key not in weeks:
            weeks[week_key] = {"quality": [], "relevance": []}

        if eval.get("quality_score"):
            weeks[week_key]["quality"].append(eval["quality_score"])
        if eval.get("relevance_score"):
            weeks[week_key]["relevance"].append(eval["relevance_score"])

    print("\nSemana | Calidad (avg) | Relevancia (avg)")
    print("-" * 50)

    for week in sorted(weeks.keys()):
        q_avg = statistics.mean(weeks[week]["quality"]) if weeks[week]["quality"] else None
        r_avg = statistics.mean(weeks[week]["relevance"]) if weeks[week]["relevance"] else None

        q_str = f"{q_avg:.2f}/5" if q_avg else "—"
        r_str = f"{r_avg:.2f}/5" if r_avg else "—"

        print(f"{week}  | {q_str:^13} | {r_str:^16}")

    first_week_key = sorted(weeks.keys())[0]
    last_week_key = sorted(weeks.keys())[-1]

    if weeks[first_week_key]["quality"] and weeks[last_week_key]["quality"]:
        first_q = statistics.mean(weeks[first_week_key]["quality"])
        last_q = statistics.mean(weeks[last_week_key]["quality"])
        change = last_q - first_q

        direction = "[+]" if change > 0 else "[-]" if change < 0 else "[=]"
        print(f"\n{direction} Cambio de calidad (primera → última semana): {change:+.2f}")


def print_latency_analysis(evaluations: list):
    """Analiza latencias."""
    print_header("ANÁLISIS DE LATENCIA", "-")

    if not evaluations:
        print("No hay datos de latencia.")
        return

    latencies = [e["latency_seconds"] for e in evaluations]

    print(f"\n[Latencia promedio] {statistics.mean(latencies):.3f}s")
    print(f"[Mínimo] {min(latencies):.3f}s")
    print(f"[Máximo] {max(latencies):.3f}s")

    if len(latencies) > 1:
        print(f"[Desv. Estándar] {statistics.stdev(latencies):.3f}s")

    sorted_latencies = sorted(latencies)
    mid = len(sorted_latencies) // 2
    q1 = sorted_latencies[mid // 2]
    q3 = sorted_latencies[mid + (len(sorted_latencies) - mid) // 2]

    print(f"\n[Distribución]")
    print(f"   25% más rápidas: < {q1:.3f}s")
    print(f"   50% medianas: {q1:.3f}s - {q3:.3f}s")
    print(f"   25% más lentas: > {q3:.3f}s")


def print_coverage_analysis(evaluations: list):
    """Analiza cobertura de documentos."""
    print_header("ANÁLISIS DE COBERTURA", "-")

    if not evaluations:
        print("No hay datos de cobertura.")
        return

    all_sources = {}
    for eval in evaluations:
        for source in eval.get("sources", []):
            all_sources[source] = all_sources.get(source, 0) + 1

    print(f"\n[Documentos únicos] {len(all_sources)}")
    print(f"[Total de búsquedas] {len(evaluations)}")

    if all_sources:
        print("\n[Documentos más utilizados]")
        sorted_sources = sorted(all_sources.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (source, count) in enumerate(sorted_sources, 1):
            pct = (count / len(evaluations)) * 100
            print(f"  {i}. {source}: {count} veces ({pct:.0f}%)")

        avg_chunks = statistics.mean([e["chunks_retrieved"] for e in evaluations])
        print(f"\n[Promedio de chunks] {avg_chunks:.1f}")


def print_summary(evaluations: list):
    """Imprime un resumen ejecutivo."""
    print_header("[>>] RESUMEN EJECUTIVO", "=")

    if not evaluations:
        print("[!] No hay evaluaciones registradas aún.")
        print("   Ejecuta: pipenv run python evaluar.py")
        return

    print(f"\n[OK] Total de evaluaciones: {len(evaluations)}")

    with_quality = sum(1 for e in evaluations if e.get("quality_score"))
    with_relevance = sum(1 for e in evaluations if e.get("relevance_score"))

    print(f"[Calidad] {with_quality}/{len(evaluations)}")
    print(f"[Relevancia] {with_relevance}/{len(evaluations)}")

    quality_scores = [e["quality_score"] for e in evaluations if e.get("quality_score")]
    relevance_scores = [e["relevance_score"] for e in evaluations if e.get("relevance_score")]

    if quality_scores:
        avg_quality = statistics.mean(quality_scores)
        status = "[OK]" if avg_quality >= 4 else "[WARN]" if avg_quality >= 3 else "[ERROR]"
        print(f"\n[Calidad promedio] {avg_quality:.2f}/5 {status}")

    if relevance_scores:
        avg_relevance = statistics.mean(relevance_scores)
        status = "[OK]" if avg_relevance >= 4 else "[WARN]" if avg_relevance >= 3 else "[ERROR]"
        print(f"[Relevancia promedio] {avg_relevance:.2f}/5 {status}")

    dates = set(e["timestamp"][:10] for e in evaluations)
    print(f"\n[Período] {len(dates)} días distintos")
    print(f"   Primero: {min(dates)}")
    print(f"   Último: {max(dates)}")
