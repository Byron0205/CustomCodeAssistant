#!/usr/bin/env python3
"""
Entry point: Chat interactivo con el RAG.
Delega la lógica a src/rag/chain.py
"""

from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings

from src.rag.chain import build_chain
from src.utils.spinner import Spinner
from src.utils.markdown_formatter import render_formatted_response
from src.config import RAG_MODES, DEFAULT_MODE, LLM_PROVIDER, EMBED_PROVIDER, LLM_MODEL


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


def handle_command(cmd: str, current_mode: str):
    """
    Procesa comandos /. Retorna (action, value):
      ("exit",    None)          → salir
      ("rebuild", nuevo_modo)    → cambiar modo y reconstruir chain
      ("continue", None)         → comando manejado, seguir el loop
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
        return ("rebuild", nuevo)

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
  [bold]/exit[/bold]           Termina la sesión
""")
        return ("continue", None)

    console.print(f"[red]Comando desconocido: '{name}'. Usa /help para ver los disponibles.[/red]")
    return ("continue", None)


def main():
    current_mode = DEFAULT_MODE
    print(f'[>>] Cargando RAG... (modo: {current_mode})')
    print(f'[>>] LLM: {LLM_PROVIDER}/{LLM_MODEL} | Embeddings: {EMBED_PROVIDER}')
    rag = build_chain(current_mode)
    print('[OK] Listo. Comandos: /mode <nombre>, /modes, /help, /salir')
    print('[TIP] Enter envía · Alt+Enter nueva línea\n')

    while True:
        print("-" * 60)
        pregunta = _read_input(current_mode).strip()

        if not pregunta:
            continue

        if pregunta.startswith('/'):
            action, value = handle_command(pregunta, current_mode)
            if action == "exit":
                break
            if action == "rebuild":
                current_mode = value
                rag = build_chain(current_mode)
                console.print(f"[green][OK] Modo cambiado a: {current_mode}[/green]")
            continue

        spinner = Spinner("Pensando")
        spinner.start()

        resultado = rag.invoke({'query': pregunta})

        spinner.stop()

        console.print(f"\n[Respuesta]")
        render_formatted_response(console, resultado["result"])
        print("-" * 60)
        print("\n")


if __name__ == '__main__':
    main()
