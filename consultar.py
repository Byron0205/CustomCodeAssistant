#!/usr/bin/env python3
"""
Entry point: Chat interactivo con el RAG.
Usa streaming token a token en lugar de esperar la respuesta completa.
"""

import sys
import time
from pathlib import Path

from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings

from src.rag.chain import load_vectorstore
from src.providers import get_llm
from src.utils.spinner import Spinner
from src.config import RAG_MODES, DEFAULT_MODE, LLM_PROVIDER, EMBED_PROVIDER, LLM_MODEL, RETRIEVER_K


console = Console()

_kb = KeyBindings()

@_kb.add('enter')
def _submit(event):
    event.current_buffer.validate_and_handle()

@_kb.add('escape', 'enter')
def _newline(event):
    event.current_buffer.insert_text('\n')


def _read_input(mode: str):
    return prompt(f'[{mode}] >> ', multiline=True, key_bindings=_kb,
                  prompt_continuation='   ')


def _chunk_text(chunk) -> str:
    """Extrae texto de un chunk de streaming (string para Ollama, AIMessageChunk para Claude/OpenAI)."""
    if hasattr(chunk, 'content'):
        return chunk.content
    return str(chunk)


def handle_command(cmd: str, current_mode: str):
    """
    Procesa comandos /. Retorna (action, value):
      ("exit",     None)       → salir
      ("mode",     nuevo_modo) → cambiar modo (solo swap de prompt, sin rebuild)
      ("continue", None)       → comando manejado, seguir el loop
    """
    parts = cmd.strip().split()
    name = parts[0].lower()

    if name in ('/salir', '/exit', '/quit'):
        return ("exit", None)

    if name in ('/mode', '/modo'):
        if len(parts) < 2:
            console.print("[yellow]Uso: /mode <nombre>. Usa /modes para ver los disponibles.[/yellow]")
            return ("continue", None)
        nuevo = parts[1].lower()
        if nuevo not in RAG_MODES:
            nombres = ', '.join(RAG_MODES.keys())
            console.print(f"[red]Modo '{nuevo}' no existe. Disponibles: {nombres}[/red]")
            return ("continue", None)
        if nuevo == current_mode:
            console.print(f"[yellow]Ya estás en el modo '{nuevo}'.[/yellow]")
            return ("continue", None)
        return ("mode", nuevo)

    if name in ('/modes', '/modos'):
        console.print("\n[bold cyan]Modos disponibles:[/bold cyan]")
        for key, cfg in RAG_MODES.items():
            marker = " [green](activo)[/green]" if key == current_mode else ""
            console.print(f"  [bold]{key}[/bold] — {cfg['description']}{marker}")
        console.print()
        return ("continue", None)

    if name == '/help':
        console.print("""
[bold cyan]Comandos disponibles:[/bold cyan]
  [bold]/mode <nombre>[/bold]   Cambia el modo del asistente
  [bold]/modes[/bold]           Lista todos los modos disponibles
  [bold]/help[/bold]            Muestra esta ayuda
  [bold]/exit[/bold]            Termina la sesión
""")
        return ("continue", None)

    console.print(f"[red]Comando desconocido: '{name}'. Usa /help para ver los disponibles.[/red]")
    return ("continue", None)


def main():
    current_mode = DEFAULT_MODE

    console.print(f"[dim][>>] LLM: {LLM_PROVIDER}/{LLM_MODEL} | Embeddings: {EMBED_PROVIDER}[/dim]")

    spinner = Spinner("Cargando")
    spinner.start()
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    llm = get_llm()
    spinner.stop()

    console.print(f"[green][OK] Listo.[/green] Modo: [bold]{current_mode}[/bold]")
    console.print("[dim]Enter envía · Alt+Enter nueva línea · /help para comandos[/dim]\n")

    while True:
        print("-" * 60)
        pregunta = _read_input(current_mode).strip()

        if not pregunta:
            continue

        if pregunta.startswith('/'):
            action, value = handle_command(pregunta, current_mode)
            if action == "exit":
                break
            if action == "mode":
                current_mode = value
                console.print(f"[green][OK] Modo: [bold]{current_mode}[/bold][/green]")
            continue

        t0 = time.time()

        # Retrieval — rápido, muestra indicador breve
        sys.stdout.write('[>>] Recuperando contexto...')
        sys.stdout.flush()
        docs = retriever.invoke(pregunta)
        context = "\n\n".join([doc.page_content for doc in docs])
        sys.stdout.write('\r' + ' ' * 35 + '\r')
        sys.stdout.flush()

        # Formatear prompt con el template del modo activo
        # str.format() ignora kwargs extra, así que pasar context siempre es seguro
        prompt_text = RAG_MODES[current_mode]["prompt_template"].format(
            context=context, question=pregunta
        )

        # Streaming — mostrar indicador hasta el primer token
        console.print("\n[bold cyan][Respuesta][/bold cyan]")
        sys.stdout.write('[>>] Generando...')
        sys.stdout.flush()

        first_token = True
        for chunk in llm.stream(prompt_text):
            if first_token:
                sys.stdout.write('\r' + ' ' * 20 + '\r')
                sys.stdout.flush()
                first_token = False
            token = _chunk_text(chunk)
            print(token, end='', flush=True)

        elapsed = time.time() - t0

        # Fuentes y latencia
        source_files = sorted(set(
            Path(doc.metadata.get("source", "desconocido")).name
            for doc in docs
        ))
        sources_str = ', '.join(source_files) if source_files else 'ninguna'

        print()
        console.print(f"\n[dim]Fuentes: {sources_str} | {elapsed:.1f}s[/dim]")
        print()


if __name__ == '__main__':
    main()
