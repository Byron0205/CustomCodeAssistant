"""
Helper JSONL compartido — append-only y lector con guards.
Centraliza el patrón duplicado en metrics/evaluator.py y metrics/progress.py.
"""

import json
from pathlib import Path


def append_jsonl(path, obj: dict):
    """Agrega una línea JSON al final del archivo (append-only)."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_jsonl(path) -> list:
    """Lee todas las entradas de un archivo JSONL. Retorna [] si no existe."""
    path = Path(path)
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries
