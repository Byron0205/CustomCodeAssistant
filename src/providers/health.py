"""
Health-check, auto-arranque y reconexión para Ollama.
Solo aplica cuando LLM_PROVIDER o EMBED_PROVIDER == "ollama".
Para Claude/OpenAI (APIs remotas) preflight() retorna True de inmediato.
"""

import os
import sys
import shutil
import subprocess
import time


# ---------------------------------------------------------------------------
# Funciones de bajo nivel (sin prints, puro estado)
# ---------------------------------------------------------------------------

def is_ollama_up(base_url: str, timeout: float = 2.0) -> bool:
    """Ping liviano al server de Ollama. Nunca lanza excepciones."""
    try:
        import ollama
        client = ollama.Client(host=base_url, timeout=timeout)
        client.list()
        return True
    except Exception:
        return False


def installed_models(base_url: str) -> set:
    """
    Retorna el conjunto de modelos descargados en Ollama.
    Incluye nombre completo ('mistral:7b') y base ('mistral') para matching flexible.
    """
    try:
        import ollama
        client = ollama.Client(host=base_url, timeout=5.0)
        response = client.list()
        names = set()
        for m in response.models:
            name = getattr(m, 'model', '') or getattr(m, 'name', '')
            if name:
                names.add(name)
                if ':' in name:
                    names.add(name.split(':')[0])  # ej: "mistral" de "mistral:7b"
        return names
    except Exception:
        return set()


def missing_models(base_url: str, required: list) -> list:
    """Retorna los modelos requeridos que NO están descargados."""
    if not required:
        return []
    inst = installed_models(base_url)
    faltantes = []
    for model in required:
        base = model.split(':')[0] if ':' in model else model
        if model not in inst and base not in inst:
            faltantes.append(model)
    return faltantes


def required_ollama_models() -> list:
    """Deriva los modelos requeridos según LLM_PROVIDER y EMBED_PROVIDER de config."""
    from src.config import LLM_PROVIDER, EMBED_PROVIDER, LLM_MODEL, EMBED_MODEL
    models = []
    if LLM_PROVIDER == "ollama":
        models.append(LLM_MODEL)
    if EMBED_PROVIDER == "ollama" and EMBED_MODEL not in models:
        models.append(EMBED_MODEL)
    return models


def start_ollama() -> bool:
    """
    Lanza 'ollama serve' en segundo plano de forma detached.
    Retorna True si pudo lanzarlo, False si el binario no existe o falló.
    """
    if not shutil.which("ollama"):
        return False
    try:
        if os.name == 'nt':
            # Windows: proceso completamente independiente del parent
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Orquestador: ensure_ollama
# ---------------------------------------------------------------------------

def ensure_ollama(
    base_url: str,
    required_models: list,
    autostart: bool = True,
    wait: int = 15,
) -> tuple:
    """
    Verifica que Ollama esté corriendo y los modelos necesarios descargados.
    Si está caído y autostart=True, intenta levantarlo y espera hasta `wait` segundos.
    Imprime progreso de arranque con puntos.

    Retorna (ok: bool, problems: list[str]).
    """
    # Server ya está corriendo
    if is_ollama_up(base_url):
        faltantes = missing_models(base_url, required_models)
        if not faltantes:
            return True, []
        return False, [
            f"Modelo faltante: '{m}' — ejecuta: ollama pull {m}" for m in faltantes
        ]

    # Server caído, sin autostart
    if not autostart:
        return False, ["Ollama no está corriendo. Ejecuta: ollama serve"]

    # Ollama no instalado
    if not shutil.which("ollama"):
        return False, [
            "Ollama no está instalado o no está en el PATH.",
            "Descárgalo desde: https://ollama.com/download",
        ]

    # Intentar levantar
    print("[>>] Iniciando Ollama", end="", flush=True)
    if not start_ollama():
        print()
        return False, ["No se pudo iniciar Ollama. Ejecuta manualmente: ollama serve"]

    # Polling hasta que responda
    for i in range(wait):
        time.sleep(1)
        if (i + 1) % 3 == 0:
            print(".", end="", flush=True)
        if is_ollama_up(base_url):
            print()
            faltantes = missing_models(base_url, required_models)
            if not faltantes:
                return True, []
            return False, [
                f"Modelo faltante: '{m}' — ejecuta: ollama pull {m}" for m in faltantes
            ]

    print()
    return False, [f"Ollama no respondió en {wait}s. Ejecuta manualmente: ollama serve"]


# ---------------------------------------------------------------------------
# Punto de entrada público: preflight
# ---------------------------------------------------------------------------

def preflight(verbose: bool = True) -> bool:
    """
    Verifica Ollama al arrancar. Reutilizable por consultar.py, indexar.py, evaluar.py.
    - Si ningún provider es ollama: retorna True de inmediato.
    - Si Ollama está caído: intenta levantarlo automáticamente.
    - Si falla: muestra errores y ofrece loop Reintentar / Salir.
    Retorna True solo cuando Ollama está completamente listo.
    """
    from src.config import LLM_PROVIDER, EMBED_PROVIDER, OLLAMA_BASE_URL, OLLAMA_AUTOSTART, OLLAMA_STARTUP_WAIT

    # No aplica para providers remotos
    if LLM_PROVIDER != "ollama" and EMBED_PROVIDER != "ollama":
        return True

    required = required_ollama_models()

    while True:
        ok, problems = ensure_ollama(
            OLLAMA_BASE_URL,
            required,
            autostart=OLLAMA_AUTOSTART,
            wait=OLLAMA_STARTUP_WAIT,
        )

        if ok:
            return True

        if not verbose:
            return False

        print()
        for p in problems:
            print(f"[!] {p}")
        print()

        try:
            resp = input("Reintentar [r] / Salir [q]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            resp = 'q'

        if resp != 'r':
            print("[--] Saliendo.")
            return False
