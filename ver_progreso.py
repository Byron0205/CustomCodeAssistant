#!/usr/bin/env python3
"""
Entry point: Visualización de progreso y métricas.
Delega la lógica a src/metrics/progress.py
"""

from src.metrics.progress import (
    load_evaluations,
    print_summary,
    print_latest_evaluations,
    print_quality_trend,
    print_latency_analysis,
    print_coverage_analysis,
)


def main():
    evaluations = load_evaluations()

    print("\n[>>] VISOR DE PROGRESO DEL RAG")
    print("="*70)

    while True:
        print("\n¿Qué deseas ver?")
        print("1. Resumen ejecutivo")
        print("2. Últimas evaluaciones")
        print("3. Tendencia de calidad")
        print("4. Análisis de latencia")
        print("5. Análisis de cobertura")
        print("6. Ver todo")
        print("7. Salir")

        choice = input("\nOpción (1-7): ").strip()

        if choice == "1":
            print_summary(evaluations)
        elif choice == "2":
            print_latest_evaluations(evaluations)
        elif choice == "3":
            print_quality_trend(evaluations)
        elif choice == "4":
            print_latency_analysis(evaluations)
        elif choice == "5":
            print_coverage_analysis(evaluations)
        elif choice == "6":
            print_summary(evaluations)
            print_latest_evaluations(evaluations, limit=10)
            print_quality_trend(evaluations)
            print_latency_analysis(evaluations)
            print_coverage_analysis(evaluations)
        elif choice == "7":
            print("\n[--] Hasta luego")
            break
        else:
            print("[!] Opción inválida")


if __name__ == "__main__":
    main()
