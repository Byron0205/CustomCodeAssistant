#!/usr/bin/env python3
"""
Entry point: Chat interactivo con el RAG.
Soporta múltiples chats persistentes con historial de conversación.
"""

import sys
import time
from pathlib import Path

from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter

from src.rag.chain import load_vectorstore
from src.providers import get_llm
from src.providers.health import preflight, ensure_ollama, is_ollama_up, required_ollama_models
from src.utils.spinner import Spinner
from src.utils.markdown_formatter import create_rich_table
from src.chat.store import list_chats, create_chat, load_chat, delete_chat
from src.config import (
    RAG_MODES, DEFAULT_MODE,
    LLM_PROVIDER, EMBED_PROVIDER, LLM_MODEL, EMBED_MODEL,
    RETRIEVER_K, DATA_DIR, MAX_HISTORY_TURNS,
    OLLAMA_BASE_URL, OLLAMA_AUTOSTART, OLLAMA_STARTUP_WAIT,
)


console = Console()

_kb = KeyBindings()

@_kb.add('enter')
def _submit(event):
    event.current_buffer.validate_and_handle()

@_kb.add('escape', 'enter')
def _newline(event):
    event.current_buffer.insert_text('\n')


_history = FileHistory(str(DATA_DIR / '.rag_history'))

_completer = WordCompleter(
    [
        '/mode', '/modes', '/config', '/help', '/exit', '/salir',
        '/new', '/nuevo', '/chats', '/open', '/cargar',
        '/rename', '/delete', '/borrar', '/clear', '/limpiar',
        '/history', '/historial', '/reconnect', '/reconectar',
        *RAG_MODES.keys(),
    ],
    sentence=True,
)

# Cache del último listado de /chats para resolver /open <n> y /delete <n>
_last_chat_list: list[dict] = []


def _read_input(mode: str) -> str:
    return prompt(
        f'[{mode}] >> ',
        multiline=True,
        key_bindings=_kb,
        prompt_continuation='   ',
        history=_history,
        completer=_completer,
    )


def _chunk_text(chunk) -> str:
    """Extrae texto de un chunk de streaming (str para Ollama, AIMessageChunk para Claude/OpenAI)."""
    if hasattr(chunk, 'content'):
        return chunk.content
    return str(chunk)


def _resolve_chat_ref(ref: str) -> str | None:
    """Resuelve un número de índice o id de chat a un chat_id. None si inválido."""
    if ref.isdigit():
        idx = int(ref) - 1
        if 0 <= idx < len(_last_chat_list):
            return _last_chat_list[idx]["id"]
        return None
    return ref  # tratar como id directo


def handle_command(cmd: str, current_mode: str, session):
    """
    Procesa comandos /. Retorna (action, value):
      ("exit",    None)       → salir
      ("mode",    nuevo_modo) → cambiar modo
      ("new",     None)       → crear chat nuevo
      ("open",    chat_id)    → abrir chat existente
      ("rename",  title)      → renombrar chat activo
      ("delete",  chat_id)    → eliminar chat
      ("clear",   None)       → limpiar chat activo
      ("continue", None)      → comando manejado, seguir el loop
    """
    global _last_chat_list

    parts = cmd.strip().split(None, 1)  # máx 2 partes para preservar espacios en títulos
    name = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    # --- Salir ---
    if name in ('/salir', '/exit', '/quit'):
        return ("exit", None)

    # --- Gestión de chats ---
    if name in ('/new', '/nuevo'):
        return ("new", None)

    if name == '/chats':
        chats = list_chats()
        _last_chat_list = chats
        if not chats:
            console.print("[dim]No hay chats guardados aún.[/dim]\n")
        else:
            rows = []
            for i, m in enumerate(chats, 1):
                updated = m.get("updated", "")[:16].replace("T", " ")
                marker = " ★" if m["id"] == session.id else ""
                rows.append([
                    str(i),
                    m["title"][:38] + marker,
                    str(m["message_count"]),
                    updated,
                ])
            table = create_rich_table(["#", "Título", "Msgs", "Actualizado"], rows)
            console.print(table)
            console.print("[dim]  /open <n> para abrir · /delete <n> para eliminar[/dim]\n")
        return ("continue", None)

    if name in ('/open', '/cargar'):
        if not arg:
            console.print("[yellow]Uso: /open <n> o /open <id>[/yellow]")
            return ("continue", None)
        chat_id = _resolve_chat_ref(arg)
        if not chat_id:
            console.print(f"[red]Referencia inválida: '{arg}'. Usa /chats para ver los disponibles.[/red]")
            return ("continue", None)
        return ("open", chat_id)

    if name == '/rename':
        if not arg:
            console.print("[yellow]Uso: /rename <nuevo título>[/yellow]")
            return ("continue", None)
        return ("rename", arg)

    if name in ('/delete', '/borrar'):
        if not arg:
            console.print("[yellow]Uso: /delete <n> o /delete <id>[/yellow]")
            return ("continue", None)
        chat_id = _resolve_chat_ref(arg)
        if not chat_id:
            console.print(f"[red]Referencia inválida: '{arg}'. Usa /chats para ver los disponibles.[/red]")
            return ("continue", None)
        return ("delete", chat_id)

    if name in ('/clear', '/limpiar'):
        return ("clear", None)

    if name in ('/reconnect', '/reconectar'):
        return ("reconnect", None)

    if name in ('/history', '/historial'):
        if not session.messages:
            console.print("[dim]Este chat no tiene mensajes todavía.[/dim]\n")
        else:
            console.print(f"\n[bold cyan]Historial:[/bold cyan] {session.title}")
            console.print(f"[dim]{'─' * 58}[/dim]")
            for i, msg in enumerate(session.messages, 1):
                ts = msg.get("timestamp", "")[:16].replace("T", " ")
                if msg["role"] == "user":
                    console.print(f"[cyan][{i}] Tú ({ts})[/cyan]")
                else:
                    console.print(f"[white][{i}] RAG ({ts})[/white]")
                preview = msg["content"][:250] + ("…" if len(msg["content"]) > 250 else "")
                console.print(f"    {preview}\n")
        return ("continue", None)

    # --- Modo ---
    if name in ('/mode', '/modo'):
        if not arg:
            console.print("[yellow]Uso: /mode <nombre>. Usa /modes para ver los disponibles.[/yellow]")
            return ("continue", None)
        nuevo = arg.lower()
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

    # --- Info ---
    if name == '/config':
        ollama_line = ""
        if LLM_PROVIDER == "ollama" or EMBED_PROVIDER == "ollama":
            up = is_ollama_up(OLLAMA_BASE_URL)
            status = "[green]activo[/green]" if up else "[red]caído[/red]"
            autostart = "on" if OLLAMA_AUTOSTART else "off"
            ollama_line = f"\n  Ollama:     {status} | autostart {autostart}"
        console.print(f"""
[bold cyan]Configuración activa:[/bold cyan]
  LLM:        [bold]{LLM_PROVIDER}[/bold] / {LLM_MODEL}
  Embeddings: [bold]{EMBED_PROVIDER}[/bold] / {EMBED_MODEL}
  Retriever:  top-{RETRIEVER_K} chunks · ventana {MAX_HISTORY_TURNS} turnos
  Modo:       [bold]{current_mode}[/bold] — {RAG_MODES[current_mode]['description']}
  Chat:       [bold]{session.title}[/bold] ({session.message_count} mensajes){ollama_line}
""")
        return ("continue", None)

    if name == '/help':
        console.print("""
[bold cyan]Comandos disponibles:[/bold cyan]

[bold]Chats:[/bold]
  [bold]/new[/bold]              Crea un chat nuevo
  [bold]/chats[/bold]            Lista todos los chats
  [bold]/open <n|id>[/bold]      Abre un chat por número o id
  [bold]/rename <título>[/bold]  Renombra el chat activo
  [bold]/delete <n|id>[/bold]    Elimina un chat (permanente)
  [bold]/clear[/bold]            Limpia el historial del chat activo
  [bold]/history[/bold]          Muestra los turnos del chat activo

[bold]Modo:[/bold]
  [bold]/mode <nombre>[/bold]    Cambia el modo del asistente
  [bold]/modes[/bold]            Lista todos los modos disponibles

[bold]Sistema:[/bold]
  [bold]/reconnect[/bold]        Reconecta con Ollama si se cayó (sin reiniciar)
  [bold]/config[/bold]           Muestra proveedor, modelo y chat activos
  [bold]/help[/bold]             Muestra esta ayuda
  [bold]/exit[/bold]             Termina la sesión

[dim]Tab autocompleta comandos · ↑↓ navega historial de inputs[/dim]
""")
        return ("continue", None)

    console.print(f"[red]Comando desconocido: '{name}'. Usa /help para ver los disponibles.[/red]")
    return ("continue", None)


def main():
    current_mode = DEFAULT_MODE

    console.print(f"[dim][>>] LLM: {LLM_PROVIDER}/{LLM_MODEL} | Embeddings: {EMBED_PROVIDER}[/dim]")

    # Verificar Ollama antes de cargar (se omite si el provider es Claude/OpenAI)
    if not preflight():
        sys.exit(0)

    spinner = Spinner("Cargando")
    spinner.start()
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    llm = get_llm()
    spinner.stop()

    # Auto-cargar el chat más reciente o crear uno nuevo
    chats = list_chats()
    if chats:
        session = load_chat(chats[0]["id"])
        current_mode = session.mode
        console.print(
            f"[green][OK] Listo.[/green] "
            f"Chat: [bold]{session.title}[/bold] ({session.message_count} msgs)"
        )
    else:
        session = create_chat(current_mode)
        console.print("[green][OK] Listo.[/green] Nuevo chat iniciado.")

    console.print("[dim]Enter envía · Alt+Enter nueva línea · /help para comandos[/dim]\n")

    while True:
        # Separador con título del chat activo
        title_display = session.title[:42]
        console.print(f"[dim]{'─' * 4} {title_display} {'─' * max(0, 54 - len(title_display))}[/dim]")

        pregunta = _read_input(current_mode).strip()

        if not pregunta:
            continue

        if pregunta.startswith('/'):
            action, value = handle_command(pregunta, current_mode, session)

            if action == "exit":
                break

            elif action == "mode":
                current_mode = value
                session.set_mode(value)
                console.print(f"[green][OK] Modo: [bold]{current_mode}[/bold][/green]")

            elif action == "new":
                session = create_chat(current_mode)
                console.print(f"[green][OK] Nuevo chat iniciado.[/green]")

            elif action == "open":
                try:
                    session = load_chat(value)
                    current_mode = session.mode
                    console.print(
                        f"[green][OK] Chat abierto:[/green] [bold]{session.title}[/bold] "
                        f"({session.message_count} mensajes)"
                    )
                except ValueError as e:
                    console.print(f"[red]{e}[/red]")

            elif action == "rename":
                session.rename(value)
                console.print(f"[green][OK] Renombrado a:[/green] [bold]{session.title}[/bold]")

            elif action == "delete":
                was_active = (value == session.id)
                delete_chat(value)
                if was_active:
                    remaining = list_chats()
                    if remaining:
                        session = load_chat(remaining[0]["id"])
                        current_mode = session.mode
                        console.print(
                            f"[yellow][OK] Chat eliminado.[/yellow] "
                            f"Activo: [bold]{session.title}[/bold]"
                        )
                    else:
                        session = create_chat(current_mode)
                        console.print("[yellow][OK] Chat eliminado. Nuevo chat iniciado.[/yellow]")
                else:
                    console.print("[yellow][OK] Chat eliminado.[/yellow]")

            elif action == "clear":
                session.clear()
                console.print("[yellow][OK] Historial del chat limpiado.[/yellow]")

            elif action == "reconnect":
                if LLM_PROVIDER != "ollama" and EMBED_PROVIDER != "ollama":
                    console.print("[dim]No aplica: el proveedor activo no es Ollama.[/dim]")
                else:
                    ok, problems = ensure_ollama(
                        OLLAMA_BASE_URL, required_ollama_models(),
                        autostart=OLLAMA_AUTOSTART, wait=OLLAMA_STARTUP_WAIT,
                    )
                    if ok:
                        console.print("[green][OK] Ollama listo. Puedes continuar.[/green]")
                    else:
                        for p in problems:
                            console.print(f"[red][!] {p}[/red]")

            continue

        # ── Turno de conversación ──────────────────────────────────────────

        # 1. Historial ANTES de agregar el mensaje actual
        history = session.history_block(MAX_HISTORY_TURNS)

        # 2. Persistir mensaje del usuario (auto-setea título en el 1er turno)
        session.append("user", pregunta)

        t0 = time.time()

        # 3. Retrieval — solo sobre la pregunta actual (con reintento tras reconexión)
        sys.stdout.write('[>>] Recuperando contexto...')
        sys.stdout.flush()
        docs = None
        for _attempt in range(2):
            try:
                docs = retriever.invoke(pregunta)
                break
            except ConnectionError:
                sys.stdout.write('\r' + ' ' * 35 + '\r')
                sys.stdout.flush()
                if _attempt == 0:
                    console.print("[yellow][!] Conexión perdida. Reconectando...[/yellow]")
                    ok, problems = ensure_ollama(
                        OLLAMA_BASE_URL, required_ollama_models(),
                        autostart=OLLAMA_AUTOSTART, wait=10,
                    )
                    if ok:
                        console.print("[green][OK] Reconectado. Reintentando...[/green]")
                        sys.stdout.write('[>>] Recuperando contexto...')
                        sys.stdout.flush()
                        continue
                    for p in problems:
                        console.print(f"[red]    {p}[/red]")
                    console.print("[dim]    Usa /reconnect cuando Ollama esté listo.[/dim]\n")
                else:
                    console.print("[red][!] Sigue sin responder. Usa /reconnect cuando Ollama esté listo.[/red]\n")
                break
            except Exception as e:
                sys.stdout.write('\r' + ' ' * 35 + '\r')
                sys.stdout.flush()
                console.print(f"[red][!] Error en retrieval: {e}[/red]\n")
                break

        if docs is None:
            continue

        context = "\n\n".join([doc.page_content for doc in docs])
        sys.stdout.write('\r' + ' ' * 35 + '\r')
        sys.stdout.flush()

        # 4. Formatear prompt con contexto + historial
        # str.format() ignora kwargs extra → pasar history siempre es seguro (ej: modo refine)
        prompt_text = RAG_MODES[current_mode]["prompt_template"].format(
            context=context, question=pregunta, history=history
        )

        # 5. Streaming con buffer y reintento tras reconexión
        console.print("\n[bold cyan][Respuesta][/bold cyan]")
        sys.stdout.write('[>>] Generando...')
        sys.stdout.flush()

        full_response = ""
        first_token = True
        stream_ok = False
        for _attempt in range(2):
            try:
                for chunk in llm.stream(prompt_text):
                    if first_token:
                        sys.stdout.write('\r' + ' ' * 20 + '\r')
                        sys.stdout.flush()
                        first_token = False
                    token = _chunk_text(chunk)
                    print(token, end='', flush=True)
                    full_response += token
                stream_ok = True
                break
            except ConnectionError:
                sys.stdout.write('\r' + ' ' * 20 + '\r')
                sys.stdout.flush()
                if _attempt == 0:
                    console.print("\n[yellow][!] Conexión perdida con el LLM. Reconectando...[/yellow]")
                    ok, problems = ensure_ollama(
                        OLLAMA_BASE_URL, required_ollama_models(),
                        autostart=OLLAMA_AUTOSTART, wait=10,
                    )
                    if ok:
                        console.print("[green][OK] Reconectado. Reintentando generación...[/green]")
                        full_response = ""   # reiniciar buffer
                        first_token = True
                        sys.stdout.write('[>>] Generando...')
                        sys.stdout.flush()
                        continue
                    for p in problems:
                        console.print(f"[red]    {p}[/red]")
                    console.print("[dim]    Usa /reconnect cuando Ollama esté listo.[/dim]")
                else:
                    console.print("[red][!] Sigue sin responder. Usa /reconnect cuando Ollama esté listo.[/red]")
                break
            except Exception as e:
                sys.stdout.write('\r' + ' ' * 20 + '\r')
                sys.stdout.flush()
                console.print(f"\n[red][!] Error durante la generación: {e}[/red]")
                break

        if not stream_ok:
            print()
            continue

        elapsed = time.time() - t0

        # 6. Fuentes y latencia
        source_files = sorted(set(
            Path(doc.metadata.get("source", "desconocido")).name
            for doc in docs
        ))
        sources_str = ', '.join(source_files) if source_files else 'ninguna'

        print()
        console.print(f"\n[dim]Fuentes: {sources_str} | {elapsed:.1f}s[/dim]")
        print()

        # 7. Persistir respuesta del asistente (solo si hubo respuesta)
        if full_response:
            session.append("assistant", full_response, sources=source_files, latency=round(elapsed, 2))


if __name__ == '__main__':
    main()
