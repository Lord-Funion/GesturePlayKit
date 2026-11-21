"""Camera resource handling without requiring real hardware."""
from types import SimpleNamespace
import numpy as np
import pytest
from gestureplaykit import Camera


class FakeCapture:
    def __init__(self, index):
        self.index = index
        self.released = False
        self.properties = {}
    def isOpened(self):
        return True
    def set(self, prop, value):
        self.properties[prop] = value
    def read(self):
        return True, np.arange(18, dtype=np.uint8).reshape(2, 3, 3)
    def release(self):
        self.released = True


def test_camera_lifecycle(monkeypatch):
    fake = FakeCapture(0)
    monkeypatch.setattr('gestureplaykit.camera.cv2.VideoCapture', lambda idx: fake)
    monkeypatch.setattr('gestureplaykit.camera.cv2.destroyAllWindows', lambda: None)
    monkeypatch.setattr('gestureplaykit.camera.cv2.imshow', lambda *args: None)
    monkeypatch.setattr('gestureplaykit.camera.cv2.waitKey', lambda ms: 0)
    with Camera(width=300, height=200) as cam:
        assert cam.read().shape == (2, 3, 3)
        assert cam.show(cam.read())
        with pytest.raises(ValueError):
            cam.show(cam.read(), quit_key='close')
    assert fake.released
    with pytest.raises(RuntimeError):
        cam.read()


def test_camera_fails_to_open(monkeypatch):
    fake = FakeCapture(0)
    fake.isOpened = lambda: False
    monkeypatch.setattr('gestureplaykit.camera.cv2.VideoCapture', lambda idx: fake)
    with pytest.raises(RuntimeError):
        with Camera():
            pass
    assert fake.released
