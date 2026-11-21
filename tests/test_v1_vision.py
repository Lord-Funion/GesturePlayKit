"""v1 tracking stability, event transitions and validation."""
from types import SimpleNamespace
import time

import numpy as np
import pytest

from gestureplaykit import Vision


class Tracker:
    def __init__(self, field, frames):
        self.field = field
        self.frames = list(frames)
        self.closed = False
        self.timestamps = []
    def detect_for_video(self, image, timestamp):
        self.timestamps.append(timestamp)
        return SimpleNamespace(**{self.field: self.frames.pop(0)})
    def close(self):
        self.closed = True


class FakeImage:
    def __init__(self, **kwargs):
        pass


def p(x, y):
    return SimpleNamespace(x=x, y=y)


def hand(x, pinch=False):
    points = [p(x, 0.5) for _ in range(21)]
    points[5] = p(x - 0.10, .5)
    points[17] = p(x + 0.10, .5)
    points[4] = p(x - 0.04, .4)
    points[8] = p(x - 0.02 if pinch else x + 0.18, .4)
    return points


def ready_vision(monkeypatch, hands_frames, face_frames=None):
    v = Vision(hands=True, faces=face_frames is not None)
    v._mp = SimpleNamespace(Image=FakeImage, ImageFormat=SimpleNamespace(SRGB=1))
    v._hands_tracker = Tracker('hand_landmarks', hands_frames)
    if face_frames is not None:
        v._faces_tracker = Tracker('face_landmarks', face_frames)
    v._start = 0
    ticks = iter(1 + i * 0.15 for i in range(len(hands_frames)))
    monkeypatch.setattr('gestureplaykit.vision.time.monotonic', lambda: next(ticks))
    return v


def test_reordering_two_hands_keeps_identity_and_gesture_history(monkeypatch):
    v = ready_vision(monkeypatch, [
        [hand(.2, True), hand(.8, False)],
        [hand(.8, False), hand(.2, True)],
        [hand(.2, False), hand(.8, True)],
    ])
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    v.update(img)
    original_left = v.hands[0].id
    original_right = v.hands[1].id
    assert v.hands[0].pinch_started
    v.update(img)
    assert v.hands[0].id == original_right
    assert v.hands[1].id == original_left
    assert not v.hands[1].pinch_started  # same pinch, reordered results
    v.update(img)
    assert v.hands[0].id == original_left
    assert v.hands[0].pinch_ended
    assert v.hands[1].id == original_right
    assert v.hands[1].pinch_started
    v.close()


def test_missing_hand_resets_double_pinch_history(monkeypatch):
    v = ready_vision(monkeypatch, [[hand(.5, True)], [], [hand(.5, True)]])
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    v.update(img)
    assert v.hand.pinch_started
    v.update(img)
    assert v.hand is None
    v.update(img)
    assert v.hand.pinch_started and not v.hand.double_pinched
    v.close()


def test_configuration_errors_and_input_frame_validation(monkeypatch):
    for config in ({'hands': False, 'faces': False},
                   {'max_hands': 0},
                   {'pinch_start': .8, 'pinch_release': .5},
                   {'mouth_closed_ratio': .8, 'mouth_open_ratio': .2},
                   {'double_pinch_window': .01}):
        with pytest.raises(ValueError):
            Vision(**config)
    v = ready_vision(monkeypatch, [[hand(.5, False)]])
    with pytest.raises(ValueError):
        v.update(np.zeros((10, 10), dtype=np.uint8))
    with pytest.raises(ValueError):
        v.update(np.zeros((10, 10, 3), dtype=np.float32))
    v.close()


def test_reset_and_close_are_safe(monkeypatch):
    v = ready_vision(monkeypatch, [[hand(.5, True)]])
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    v.update(img)
    assert v.hand is not None
    hand_tracker = v._hands_tracker
    v.reset()
    assert v.hand is None and not v.hands
    v.close()
    v.close()
    assert hand_tracker.closed
    with pytest.raises(RuntimeError):
        v.update(img)
