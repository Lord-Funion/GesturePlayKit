"""Audio API tests: no speaker or sound device needed."""
from __future__ import annotations
import io
import math
import sys
import types
import wave

import pytest
from gestureplaykit import (
    available_effects, mute_sounds, play_effect, play_sound, set_sounds_enabled,
    sounds_enabled, stop_sounds, toggle_sounds, unmute_sounds,
)
from gestureplaykit import audio


@pytest.fixture(autouse=True)
def restore_audio(monkeypatch):
    monkeypatch.setattr(audio, "_USED_PYGAME", False)
    monkeypatch.setattr(audio, "_USED_WINSOUND", False)
    unmute_sounds()
    yield
    unmute_sounds()


def test_switches_toggle_and_validate():
    assert sounds_enabled()
    mute_sounds()
    assert not sounds_enabled()
    assert toggle_sounds()
    assert sounds_enabled()
    assert not toggle_sounds()
    set_sounds_enabled(True)
    with pytest.raises(TypeError):
        set_sounds_enabled("no")
    assert sounds_enabled()


def test_builtin_effect_names_are_available():
    assert available_effects() == ("pop", "chomp", "success", "error")
    with pytest.raises(ValueError, match="Unknown effect"):
        play_effect("nonexistent")


@pytest.mark.parametrize("name", ["pop", "chomp", "success", "error"])
def test_builtin_effect_is_well_formed_pcm_wave(name):
    data = audio._synthesize_effect(name)
    with wave.open(io.BytesIO(data), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 22050
        assert wav.getnframes() > 2000
        assert wav.readframes(wav.getnframes())
    assert data == audio._synthesize_effect(name)


def test_muted_calls_never_touch_audio_or_disk(monkeypatch, tmp_path):
    mute_sounds()
    def fail(*args, **kwargs):
        raise AssertionError("audio backend should never be used while muted")
    monkeypatch.setattr(audio, "_try_pygame", fail)
    monkeypatch.setattr(audio, "_effect_path", fail)
    assert play_sound(tmp_path / "missing.wav") is False
    assert play_effect("pop") is False


def test_malformed_volume_and_loop(tmp_path):
    for bad in (float('nan'), float('inf'), -0.1, 1.01):
        with pytest.raises(ValueError):
            play_sound(tmp_path / "missing.wav", volume=bad)
    for bad in ("1", None, True):
        with pytest.raises(TypeError):
            play_sound(tmp_path / "missing.wav", volume=bad)
    with pytest.raises(TypeError):
        play_sound(tmp_path / "missing.wav", loop=2)
    assert not play_sound(tmp_path / "missing.wav", volume=0)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        play_sound(tmp_path / "missing.wav")


def test_cross_platform_pygame_backend(monkeypatch, tmp_path):
    path = tmp_path / "ping.wav"
    path.write_bytes(audio._synthesize_effect("pop"))
    events = []

    class FakeChannel:
        def set_volume(self, value): events.append(("volume", value))

    class FakeSound:
        def __init__(self, filename): events.append(("load", filename))
        def play(self, *, loops):
            events.append(("play", loops))
            return FakeChannel()

    class FakeMixer:
        def get_init(self): return False
        def init(self): events.append(("init",))
        Sound = FakeSound
        def stop(self): events.append(("stop",))

    fake = types.SimpleNamespace(mixer=FakeMixer())
    real_import = audio.importlib.import_module
    monkeypatch.setattr(audio.importlib, "import_module", lambda name: fake if name == "pygame" else real_import(name))
    assert play_sound(path, volume=.4, loop=True)
    assert ("play", -1) in events
    assert ("volume", .4) in events
    stop_sounds()
    # FakeMixer.get_init() intentionally False; stop should not run.
    assert ("stop",) not in events


def test_windows_builtin_winsound_backend(monkeypatch, tmp_path):
    path = tmp_path / "pop.wav"
    path.write_bytes(audio._synthesize_effect("pop"))
    events = []
    fake = types.SimpleNamespace(SND_FILENAME=1, SND_ASYNC=2, SND_NODEFAULT=4, SND_LOOP=8,
                                 PlaySound=lambda *args: events.append(args))
    monkeypatch.setitem(sys.modules, "winsound", fake)
    monkeypatch.setattr(audio.sys, "platform", "win32")
    monkeypatch.setattr(audio, "_try_pygame", lambda *args: False)
    assert play_sound(path, loop=True)
    assert events[0] == (str(path), 15)
    stop_sounds()
    assert events[-1] == (None, 0)
    with pytest.raises(RuntimeError, match="Volume control requires pygame"):
        play_sound(path, volume=.3)
    mp3 = tmp_path / "not-a-wav.mp3"
    mp3.write_bytes(b"test")
    with pytest.raises(ValueError, match=".wav"):
        play_sound(mp3)


def test_no_audio_backend_message(monkeypatch, tmp_path):
    path = tmp_path / "pop.wav"
    path.write_bytes(audio._synthesize_effect("pop"))
    monkeypatch.setattr(audio.sys, "platform", "linux")
    monkeypatch.setattr(audio, "_try_pygame", lambda *args: False)
    with pytest.raises(RuntimeError, match="audio"):
        play_sound(path)


def test_builtins_dispatch_to_play_sound(monkeypatch, tmp_path):
    records = []
    monkeypatch.setattr(audio, "_effect_path", lambda name: tmp_path / (name + ".wav"))
    monkeypatch.setattr(audio, "play_sound", lambda path, volume=1.0: records.append((path.name, volume)) or True)
    assert play_effect("chomp", volume=.8)
    assert records == [("chomp.wav", .8)]
