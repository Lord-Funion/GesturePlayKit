"""Simple optional sound effects for webcam apps.

On Windows, standard WAV playback uses the built-in :mod:`winsound` module.
For volume control, multiple simultaneous sounds, or other platforms, install
``gestureplaykit[audio]`` to enable ``pygame.mixer``.

No audio device is opened during import. Sound playback is nonblocking.
"""
from __future__ import annotations

import atexit
import importlib
import io
import math
import os
from pathlib import Path
import random
import shutil
import struct
import sys
import tempfile
import wave

_ENABLED = True
_USED_PYGAME = False
_USED_WINSOUND = False
_EFFECT_DIRECTORY: Path | None = None
_EFFECT_NAMES = ("pop", "chomp", "success", "error")


def sounds_enabled() -> bool:
    """Whether sound effects are enabled (``True`` by default)."""
    return _ENABLED


def set_sounds_enabled(enabled: bool) -> None:
    """Globally enable/disable sounds. Muting stops sounds already playing."""
    if not isinstance(enabled, bool):
        raise TypeError("enabled must be True or False")
    global _ENABLED
    _ENABLED = enabled
    if not enabled:
        stop_sounds()


def mute_sounds() -> None:
    """Turn off sounds and stop current playback."""
    set_sounds_enabled(False)


def unmute_sounds() -> None:
    """Enable sounds again."""
    set_sounds_enabled(True)


def toggle_sounds() -> bool:
    """Toggle sound availability and return the resulting enabled state."""
    set_sounds_enabled(not _ENABLED)
    return _ENABLED


def _validate_volume(volume: float) -> float:
    if isinstance(volume, bool) or not isinstance(volume, (int, float)):
        raise TypeError("volume must be a number between 0 and 1")
    volume = float(volume)
    if not math.isfinite(volume) or not 0.0 <= volume <= 1.0:
        raise ValueError("volume must be between 0 and 1")
    return volume


def _try_pygame(path: Path, volume: float, loop: bool) -> bool:
    """Play with pygame if available; return False if pygame is absent.

    Audio-device failures are reported to the caller for actionable error messages.
    """
    global _USED_PYGAME
    try:
        pygame = importlib.import_module("pygame")
    except ImportError:
        return False
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    sound = pygame.mixer.Sound(str(path))
    channel = sound.play(loops=-1 if loop else 0)
    if channel is None:
        raise RuntimeError("No free pygame audio channel; call stop_sounds() or increase mixer channels")
    channel.set_volume(volume)
    _USED_PYGAME = True
    return True


def _windows_wav(path: Path, loop: bool) -> None:
    global _USED_WINSOUND
    if path.suffix.casefold() != ".wav":
        raise ValueError("Without pygame, Windows playback supports only .wav files")
    import winsound  # Windows only
    flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
    if loop:
        flags |= winsound.SND_LOOP
    winsound.PlaySound(str(path), flags)
    _USED_WINSOUND = True


def play_sound(file: str | os.PathLike[str], *, volume: float = 1.0, loop: bool = False) -> bool:
    """Play a sound file without blocking the webcam loop.

    ``volume`` ranges from 0 (silent) to 1 (full volume), but values other than
    1 require pygame. ``loop=True`` repeats until :func:`stop_sounds`.
    Returns ``False`` if effects are muted (or volume is 0); otherwise ``True``.

    Windows has a built-in WAV fallback using winsound (one sound at a time).
    For cross-platform playback, overlapping sounds, MP3/OGG, and volume, use
    the optional ``pygame`` backend: ``pip install 'gestureplaykit[audio]'``.
    """
    volume = _validate_volume(volume)
    if not isinstance(loop, bool):
        raise TypeError("loop must be True or False")
    if not _ENABLED or volume == 0:
        return False
    path = Path(file).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Sound not found: {path}")
    try:
        if _try_pygame(path, volume, loop):
            return True
    except Exception as exc:
        # A failed pygame audio device should not prevent basic WAV on Windows.
        if sys.platform != "win32" or volume != 1.0:
            raise RuntimeError(f"Pygame audio could not start: {exc}") from exc
    if sys.platform == "win32":
        if volume != 1.0:
            raise RuntimeError("Volume control requires pygame: pip install 'gestureplaykit[audio]'")
        _windows_wav(path, loop)
        return True
    raise RuntimeError(
        "No sound backend available. Install optional audio support: "
        "pip install 'gestureplaykit[audio]'"
    )


def stop_sounds() -> None:
    """Stop all effects started by GesturePlayKit without changing mute state."""
    if _USED_PYGAME:
        pygame = importlib.import_module("pygame")
        if pygame.mixer.get_init():
            pygame.mixer.stop()
    if _USED_WINSOUND and sys.platform == "win32":
        import winsound
        winsound.PlaySound(None, 0)


def available_effects() -> tuple[str, ...]:
    """List the bundled, synthesized effect names."""
    return _EFFECT_NAMES


def _synthesize_effect(name: str) -> bytes:
    """Produce a small, original 16-bit PCM WAV file, deterministically."""
    if name not in _EFFECT_NAMES:
        raise ValueError(f"Unknown effect {name!r}; choose from {', '.join(_EFFECT_NAMES)}")
    rate = 22050
    lengths = {"pop": .14, "chomp": .24, "success": .34, "error": .22}
    count = int(lengths[name] * rate)
    rng = random.Random(410)
    noise_state = 0.0
    samples = bytearray()
    for i in range(count):
        t = i / rate
        progress = i / count
        env = (1 - progress) ** 2.2
        if name == "pop":
            phase = 2 * math.pi * (620 * t - (370 / (2 * lengths[name])) * t * t)
            v = math.sin(phase) * env * 0.72
        elif name == "chomp":
            noise_state = noise_state * 0.66 + rng.uniform(-1, 1) * 0.34
            v = (noise_state * 0.67 + math.sin(2 * math.pi * 88 * t) * 0.45) * env
        elif name == "success":
            index = min(2, int(progress * 3))
            freq = (523.25, 659.25, 783.99)[index]
            local = (progress * 3) % 1
            v = math.sin(2 * math.pi * freq * t) * (1 - local) ** 0.6 * 0.58
        else:
            v = (math.sin(2 * math.pi * 210 * t) + math.sin(2 * math.pi * 232 * t)) * env * 0.29
        samples.extend(struct.pack("<h", round(max(-1.0, min(1.0, v)) * 32767)))
    output = io.BytesIO()
    with wave.open(output, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples)
    return output.getvalue()


def _effect_path(name: str) -> Path:
    global _EFFECT_DIRECTORY
    if _EFFECT_DIRECTORY is None:
        _EFFECT_DIRECTORY = Path(tempfile.mkdtemp(prefix="gestureplaykit-sounds-"))
        atexit.register(shutil.rmtree, _EFFECT_DIRECTORY, ignore_errors=True)
    path = _EFFECT_DIRECTORY / f"{name}.wav"
    if not path.exists():
        path.write_bytes(_synthesize_effect(name))
    return path


def play_effect(name: str = "pop", *, volume: float = 1.0) -> bool:
    """Play a built-in original short effect: pop, chomp, success, or error.

    Works without downloading files. Windows WAV fallback needs no audio
    dependency; other platforms need the optional pygame audio extra.
    """
    if name not in _EFFECT_NAMES:
        raise ValueError(f"Unknown effect {name!r}; choose from {', '.join(_EFFECT_NAMES)}")
    volume = _validate_volume(volume)
    if not _ENABLED or volume == 0:
        return False
    return play_sound(_effect_path(name), volume=volume)
