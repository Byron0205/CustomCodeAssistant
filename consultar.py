#!/usr/bin/env python3
"""
Entry point: Chat interactivo con el RAG.
Delega la lógica a src/rag/chain.py
"""

from rich.console import Console

from src.rag.chain import build_chain
from src.utils.spinner import Spinner
from src.utils.markdown_formatter import render_formatted_response


console = Console()


def main():
    print('[>>] Cargando RAG...')
    rag = build_chain()
    print('[OK] Listo. Escribe tu pregunta (o "salir" para terminar)\n')

    while True:
        print("-" * 60)
        pregunta = input('>> ').strip()
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            break
        if not pregunta:
            continue

        spinner = Spinner("Pensando")
        spinner.start()

        resultado = rag.invoke({'query': pregunta})

        spinner.stop()

        console.print("\n[Respuesta]")
        render_formatted_response(console, resultado["result"])

        fuentes = set(d.metadata.get('source', '?')
                      for d in resultado['source_documents'])
        console.print(f'[Fuentes: {", ".join(fuentes)}]')
        print("-" * 60)
        print("\n")


if __name__ == '__main__':
    main()
