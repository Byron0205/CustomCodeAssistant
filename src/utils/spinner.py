"""
Spinner para indicar que el sistema está procesando.
Sin dependencias externas, usa caracteres ASCII.
"""

import sys
import time
from threading import Thread


def format_elapsed(seconds: float) -> str:
    """Formatea segundos como '12.3s' o '2m 15.3s' cuando supera 60s."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds - minutes * 60
    return f"{minutes}m {secs:.1f}s"


class Spinner:
    """Spinner simple que muestra animación y contador de tiempo."""

    FRAMES = ['/', '-', '\\', '|']

    def __init__(self, message="Procesando"):
        self.message = message
        self.running = False
        self.thread = None
        self.start_time = None
        self.elapsed = 0.0

    def start(self):
        """Inicia el spinner."""
        self.running = True
        self.start_time = time.time()
        self.thread = Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        """Detiene el spinner y guarda el tiempo transcurrido en self.elapsed."""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
        sys.stdout.write('\r' + ' ' * (len(self.message) + 20) + '\r')
        sys.stdout.flush()

    def _animate(self):
        """Anima el spinner con contador de tiempo."""
        frame_idx = 0
        while self.running:
            elapsed = int(time.time() - self.start_time)
            frame = self.FRAMES[frame_idx % len(self.FRAMES)]
            sys.stdout.write(f'\r{frame} {self.message}... ({elapsed}s)')
            sys.stdout.flush()
            frame_idx += 1
            time.sleep(0.1)
