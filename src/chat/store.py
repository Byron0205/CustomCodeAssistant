"""
Almacenamiento de chats multi-sesión.

Layout en disco:
  data/chats/<id>/
    meta.json       — {id, title, mode, created, updated, message_count}
    messages.jsonl  — append-only, un mensaje por línea

Diseño de rendimiento:
- list_chats() lee solo meta.json (no carga mensajes).
- Solo el chat activo vive en RAM.
- Escritura O(1): append por mensaje, nunca reescribe el historial.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from src.config import CHATS_DIR
from src.utils.jsonl import append_jsonl, read_jsonl


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _meta_path(chat_id: str) -> Path:
    return CHATS_DIR / chat_id / "meta.json"

def _messages_path(chat_id: str) -> Path:
    return CHATS_DIR / chat_id / "messages.jsonl"

def _read_meta(chat_id: str) -> dict | None:
    path = _meta_path(chat_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_meta(chat_id: str, meta: dict):
    with open(_meta_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def list_chats() -> list[dict]:
    """
    Lista todos los chats ordenados por 'updated' descendente.
    Lee solo meta.json — no carga mensajes.
    """
    chats = []
    if not CHATS_DIR.exists():
        return chats
    for entry in CHATS_DIR.iterdir():
        if not entry.is_dir():
            continue
        meta = _read_meta(entry.name)
        if meta:
            chats.append(meta)
    return sorted(chats, key=lambda m: m.get("updated", ""), reverse=True)


def create_chat(mode: str = "default") -> "ChatSession":
    """Crea un nuevo chat vacío y retorna la sesión."""
    now = datetime.now()
    chat_id = now.strftime("%Y%m%d-%H%M%S")
    (CHATS_DIR / chat_id).mkdir(parents=True, exist_ok=True)
    meta = {
        "id": chat_id,
        "title": "Nuevo chat",
        "mode": mode,
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "message_count": 0,
    }
    _write_meta(chat_id, meta)
    return ChatSession(meta, messages=[])


def load_chat(chat_id: str) -> "ChatSession":
    """Carga un chat existente con su historial completo desde disco."""
    meta = _read_meta(chat_id)
    if not meta:
        raise ValueError(f"Chat '{chat_id}' no encontrado.")
    messages = read_jsonl(_messages_path(chat_id))
    return ChatSession(meta, messages)


def delete_chat(chat_id: str):
    """Elimina permanentemente un chat y todos sus archivos."""
    chat_dir = CHATS_DIR / chat_id
    if chat_dir.exists():
        shutil.rmtree(chat_dir)


# ---------------------------------------------------------------------------
# ChatSession — chat activo en RAM
# ---------------------------------------------------------------------------

class ChatSession:
    """
    Representa el chat activo en memoria.
    Toda escritura es append-only en disco; la RAM solo guarda el chat activo.
    """

    def __init__(self, meta: dict, messages: list):
        self._meta = meta
        self.messages = messages

    # Propiedades de solo lectura

    @property
    def id(self) -> str:
        return self._meta["id"]

    @property
    def title(self) -> str:
        return self._meta["title"]

    @property
    def mode(self) -> str:
        return self._meta["mode"]

    @property
    def message_count(self) -> int:
        return self._meta["message_count"]

    # Escritura

    def append(self, role: str, content: str, sources: list = None, latency: float = None):
        """
        Agrega un mensaje a la RAM y al disco (append-only).
        Si es el primer mensaje de usuario, auto-setea el título del chat.
        """
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if sources is not None:
            msg["sources"] = sources
        if latency is not None:
            msg["latency"] = latency

        self.messages.append(msg)
        append_jsonl(_messages_path(self.id), msg)

        # Auto-título desde el primer mensaje de usuario
        if role == "user" and self._meta["title"] == "Nuevo chat":
            titulo = content[:50].strip().replace("\n", " ")
            self._meta["title"] = titulo

        self._meta["message_count"] = len(self.messages)
        self._meta["updated"] = datetime.now().isoformat()
        _write_meta(self.id, self._meta)

    def history_block(self, max_turns: int) -> str:
        """
        Arma el bloque de texto con los últimos N turnos para inyectar al prompt.
        Llamar ANTES de append("user", ...) del turno actual.
        Retorna "" si no hay historial, o un bloque con encabezado y trailing newline.
        Cada mensaje se acota a 500 chars para no saturar la ventana del LLM.
        """
        if not self.messages:
            return ""

        window = self.messages[-(max_turns * 2):]
        if not window:
            return ""

        lines = ["Historial de la conversación (turnos recientes):"]
        for msg in window:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            content = msg["content"][:500]
            if len(msg["content"]) > 500:
                content += "..."
            lines.append(f"{role}: {content}")
        lines.append("")
        return "\n".join(lines) + "\n"

    def clear(self):
        """Vacía el historial del chat (conserva el chat). Resetea título."""
        self.messages = []
        self._meta["message_count"] = 0
        self._meta["title"] = "Nuevo chat"
        self._meta["updated"] = datetime.now().isoformat()
        _write_meta(self.id, self._meta)
        # Truncar el archivo de mensajes
        open(_messages_path(self.id), "w", encoding="utf-8").close()

    def rename(self, title: str):
        """Renombra el chat activo."""
        self._meta["title"] = title.strip()
        self._meta["updated"] = datetime.now().isoformat()
        _write_meta(self.id, self._meta)

    def set_mode(self, mode: str):
        """Actualiza el modo del chat en disco."""
        self._meta["mode"] = mode
        self._meta["updated"] = datetime.now().isoformat()
        _write_meta(self.id, self._meta)
