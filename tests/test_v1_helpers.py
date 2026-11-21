"""v1 public API, rendering, model and geometry regression tests."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from gestureplaykit import (
    Hand, Face, __version__, clamp, distance, draw_hand, inside_rectangle,
    load_picture, resize_picture, show_line, show_picture, show_rectangle,
)
from gestureplaykit import models, pictures
from gestureplaykit.__main__ import main


def make_hand():
    points = [(50, 50)] * 21
    points[0] = (50, 100)
    points[5] = (20, 75)
    points[9] = (40, 70)
    points[13] = (60, 70)
    points[17] = (80, 75)
    # Fingertips far from wrist for an open palm.
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        points[tip] = (40, 0)
        points[pip] = (40, 45)
    points[4] = (15, 20)
    points[3] = (30, 45)
    return Hand(tuple(points), False, False, False, False, id=12)


def test_version_and_geometry():
    assert __version__ == "1.2.0"
    assert distance((0, 0), (3, 4)) == 5
    assert clamp(8, 0, 5) == 5
    assert clamp(-1, 0, 5) == 0
    assert inside_rectangle((3, 4), (0, 0, 3, 4))
    assert not inside_rectangle((5, 4), (0, 0, 3, 4))
    with pytest.raises(ValueError):
        clamp(0, 2, 1)
    with pytest.raises(ValueError):
        inside_rectangle((0, 0), (3, 0, 1, 4))


def test_hand_finger_detection_and_validation():
    hand = make_hand()
    assert hand.id == 12
    assert hand.open_palm
    assert not hand.fist
    assert all(hand.fingers_up.values())
    for name in ("index", "middle", "ring", "pinky", "thumb"):
        assert hand.finger_up(name)
    with pytest.raises(ValueError):
        hand.finger_up("banana")
    with pytest.raises(ValueError):
        hand.landmark(21)
    with pytest.raises(ValueError):
        hand.landmark(-1)
    with pytest.raises(ValueError):
        hand.touching(4, 8, ratio=-0.1)
    points = list(hand.points)
    for tip in (8, 12, 16, 20):
        points[tip] = (50, 95)
    points[4] = (50, 80)
    closed = Hand(tuple(points), False, False, False, False)
    assert closed.fist and not closed.open_palm


def test_face_validations():
    pts = [(0, 0)] * 292
    pts[13], pts[14] = (20, 20), (20, 30)
    pts[61], pts[291] = (5, 25), (35, 25)
    face = Face(tuple(pts), True, True, False, 0.3)
    assert face.near_mouth((20, 25))
    with pytest.raises(ValueError):
        face.landmark(999)
    with pytest.raises(ValueError):
        face.near_mouth((0, 0), -1)


def test_picture_resizing_and_opacity():
    base = np.zeros((12, 12, 3), dtype=np.uint8)
    patch = np.full((5, 5, 4), 100, dtype=np.uint8)
    patch[:, :, 3] = 255
    assert resize_picture(patch, (3, 3)).shape == (3, 3, 4)
    assert show_picture(base, patch, at=(5, 5), opacity=0.5) is base
    assert base[5, 5, 0] == 50
    assert show_picture(base, patch, at=(-30, -30)) is base
    assert show_picture(base, patch, at=(5, 5), opacity=0) is base
    with pytest.raises(ValueError):
        show_picture(base, patch, (5, 5), opacity=2)
    with pytest.raises(ValueError):
        resize_picture(patch, (0, 3))
    with pytest.raises(ValueError):
        show_picture(base, np.ones((3, 3), dtype=np.uint8), (5, 5))


def test_line_rectangle_and_landmarks():
    frame = np.zeros((140, 140, 3), dtype=np.uint8)
    assert show_line(frame, (5, 5), (30, 30)) is frame
    assert show_rectangle(frame, (40, 40, 70, 70), fill=True) is frame
    assert draw_hand(frame, make_hand(), number_landmarks=True) is frame
    assert np.any(frame)
    with pytest.raises(ValueError):
        draw_hand(frame, [(0, 0)])


def test_model_downloading_selected_and_idempotent(monkeypatch, tmp_path):
    class FakeResponse:
        def __init__(self):
            self.data = BytesIO(b"m" * 2048)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, n):
            return self.data.read(n)
    called = []
    def fake_urlopen(request, timeout):
        called.append((request.full_url, timeout))
        return FakeResponse()
    monkeypatch.setattr(models, "urlopen", fake_urlopen)
    paths = models.download_models(tmp_path, hands=True, faces=False)
    assert len(paths) == 1
    assert paths[0].name == "hand_landmarker.task"
    assert paths[0].stat().st_size == 2048
    assert models.download_models(tmp_path, hands=True, faces=False) == paths
    assert len(called) == 1
    with pytest.raises(ValueError):
        models.download_models(tmp_path, hands=False, faces=False)


def test_image_url_caches_downloads(monkeypatch):
    png = cv2.imencode('.png', np.full((2, 3, 4), 255, np.uint8))[1].tobytes()
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, n):
            return png
    called = []
    def fake_open(request, timeout):
        called.append(request.full_url)
        return FakeResponse()
    monkeypatch.setattr(pictures, "urlopen", fake_open)
    pictures._load_source.cache_clear()
    url = 'https://example.org/test-sprite.png'
    first = load_picture(url)
    first[0, 0] = 0
    second = load_picture(url)
    assert np.all(second[0, 0] == 255)  # cache isn't accidentally mutable
    assert called == [url]
    pictures._load_source.cache_clear()


def test_cli(monkeypatch, tmp_path, capsys):
    assert main([]) == 0
    assert 'download-models' in capsys.readouterr().out
    called = []
    monkeypatch.setattr('gestureplaykit.__main__.download_models',
                        lambda folder, **kw: called.append((folder, kw)) or (Path('hand.task'),))
    assert main(['download-models', '--dir', str(tmp_path), '--hands-only']) == 0
    assert called[0][0] == str(tmp_path)
    assert called[0][1] == {'overwrite': False, 'hands': True, 'faces': False}
