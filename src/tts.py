"""Texto a voz con Edge TTS + reproducción con pygame."""
import hashlib
import asyncio
import threading
from pathlib import Path
from typing import Optional

import edge_tts
import pygame

from .config import AUDIO_DIR


_mixer_lock = threading.Lock()
_mixer_inicializado = False


def _inicializar_mixer() -> bool:
    """Inicializa pygame.mixer una sola vez."""
    global _mixer_inicializado
    if _mixer_inicializado:
        return True
    try:
        pygame.mixer.init()
        _mixer_inicializado = True
    except Exception as e:
        print(f"[tts] pygame.mixer.init falló: {e}")
        return False
    return True


def _hash_clave(texto: str, voz: str, velocidad: float) -> str:
    base = f"{voz}|{velocidad}|{texto}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def generar_audio(texto: str, voz: str, velocidad: float = 1.0) -> Path:
    """
    Genera un MP3 con edge-tts. Cachea por (texto, voz, velocidad).
    `velocidad`: 0.8 = más lento, 1.3 = más rápido.
    """
    texto = texto.strip()
    if not texto:
        raise ValueError("Texto vacío para TTS")

    clave = _hash_clave(texto, voz, velocidad)
    destino = AUDIO_DIR / f"{clave}.mp3"
    if destino.exists():
        return destino

    # Edge TTS espera un rate en formato "+10%" o "-20%"
    rate_pct = int(round((velocidad - 1.0) * 100))
    rate = f"{rate_pct:+d}%"

    async def _run():
        communicate = edge_tts.Communicate(texto, voice=voz, rate=rate)
        await communicate.save(str(destino))

    asyncio.run(_run())
    return destino


def reproducir(path: Path) -> bool:
    """Reproduce el MP3 en segundo plano. Detiene cualquier reproducción previa."""
    if not _inicializar_mixer():
        return False
    with _mixer_lock:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            return True
        except Exception as e:
            print(f"[tts] No se pudo reproducir: {e}")
            return False


def detener() -> None:
    if _mixer_inicializado:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


def esta_reproduciendo() -> bool:
    if not _mixer_inicializado:
        return False
    try:
        return pygame.mixer.music.get_busy()
    except Exception:
        return False