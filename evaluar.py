#!/usr/bin/env python3
"""
Entry point: Evaluación de métricas del RAG.
Delega la lógica a src/metrics/evaluator.py
"""

import json
from src.config import STATS_FILE
from src.metrics.evaluator import (
    load_qa_chain,
    evaluate_question,
    rate_evaluation,
    save_evaluation,
    load_evaluations,
    calculate_statistics,
    print_statistics,
    EVAL_QUESTIONS,
)


def main():
    print("[>>] EVALUADOR DE MÉTRICAS DEL RAG")
    print("="*70)

    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Evaluar preguntas predefinidas")
        print("2. Hacer una pregunta personalizada")
        print("3. Ver estadísticas")
        print("4. Salir")

        choice = input("\nOpción (1-4): ").strip()

        if choice == "1":
            print("\n[>>] Evaluando preguntas predefinidas...\n")
            qa_chain = load_qa_chain()

            for i, question in enumerate(EVAL_QUESTIONS, 1):
                print(f"[{i}/{len(EVAL_QUESTIONS)}] {question}")
                evaluation = evaluate_question(qa_chain, question)

                if evaluation:
                    if rate_evaluation(evaluation):
                        save_evaluation(evaluation)
                        print("[OK] Evaluación guardada")
                    else:
                        print("[>>] Salteada")
                else:
                    print("[ERROR] Error en la evaluación")

        elif choice == "2":
            print("\n[?] Pregunta personalizada")
            question = input("Pregunta: ").strip()

            if question:
                qa_chain = load_qa_chain()
                evaluation = evaluate_question(qa_chain, question)

                if evaluation:
                    if rate_evaluation(evaluation):
                        save_evaluation(evaluation)
                        print("[OK] Evaluación guardada")
                else:
                    print("[ERROR] Error en la evaluación")

        elif choice == "3":
            evaluations = load_evaluations()
            stats = calculate_statistics(evaluations)
            print_statistics(stats)

            with open(STATS_FILE, "w") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"\n[OK] Stats guardadas en {STATS_FILE}")

        elif choice == "4":
            print("\n[--] Hasta luego")
            break

        else:
            print("[!] Opción inválida")


if __name__ == "__main__":
    main()
