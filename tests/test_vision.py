from types import SimpleNamespace
import time

import cv2
import numpy as np

from gestureplaykit import Vision


class FakeTracker:
    def __init__(self, attr, frames):
        self.attr = attr
        self.frames = list(frames)
        self.closed = False

    def detect_for_video(self, image, ts):
        return SimpleNamespace(**{self.attr: self.frames.pop(0)})

    def close(self):
        self.closed = True


class FakeImage:
    def __init__(self, **kwargs):
        pass


def landmark(x, y):
    return SimpleNamespace(x=x, y=y)


def fake_hand(pinch):
    pts = [landmark(.5, .5) for _ in range(21)]
    pts[5] = landmark(.25, .5)
    pts[17] = landmark(.75, .5)
    pts[4] = landmark(.45, .4)
    pts[8] = landmark(.47 if pinch else .9, .4)
    return pts


def fake_face(opened):
    pts = [landmark(.5, .5) for _ in range(300)]
    pts[61] = landmark(.4, .5)
    pts[291] = landmark(.6, .5)
    pts[13] = landmark(.5, .49)
    pts[14] = landmark(.5, .55 if opened else .50)
    return pts


def test_vision_events_monkeypatched(monkeypatch):
    vision = Vision()
    vision._start = 0.0
    ticks = iter([1.0, 1.10, 1.20, 1.30, 1.40])
    monkeypatch.setattr("gestureplaykit.vision.time.monotonic", lambda: next(ticks))
    vision._mp = SimpleNamespace(Image=FakeImage, ImageFormat=SimpleNamespace(SRGB=1))
    hands = FakeTracker('hand_landmarks', [
        [fake_hand(False)], [fake_hand(True)], [fake_hand(False)],
        [fake_hand(True)], []
    ])
    faces = FakeTracker('face_landmarks', [
        [fake_face(False)], [fake_face(True)], [fake_face(True)],
        [fake_face(False)], []
    ])
    vision._hands_tracker = hands
    vision._faces_tracker = faces
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    vision.update(img)
    assert not vision.hand.pinching
    vision.update(img)
    assert vision.hand.pinching and vision.hand.pinch_started
    assert vision.face.mouth_open and vision.face.mouth_just_opened
    vision.update(img)
    assert vision.hand.pinch_ended
    assert vision.face.mouth_open
    vision.update(img)
    assert vision.hand.double_pinched
    assert vision.face.mouth_just_closed
    vision.update(img)
    assert vision.hand is None and vision.face is None
    vision.close()
    assert hands.closed and faces.closed
