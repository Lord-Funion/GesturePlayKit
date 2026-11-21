from types import SimpleNamespace
from pathlib import Path

import cv2
import numpy as np
import pytest

from gestureplaykit import Hand, Face, load_picture, show_picture, show_text, show_point
from gestureplaykit.models import model_paths


def make_hand():
    pts = [(0, 0)] * 21
    pts[0] = (30, 80)
    pts[4] = (50, 40)
    pts[8] = (52, 42)
    pts[5] = (20, 50)
    pts[9] = (36, 47)
    pts[13] = (49, 49)
    pts[17] = (80, 50)
    return Hand(tuple(pts), True, True, False, False)


def test_landmark_pinch_and_palm():
    hand = make_hand()
    assert hand.pinching
    assert hand.landmark(8) == (52, 42)
    assert hand.distance(4, 8) == pytest.approx(2.828, abs=0.01)
    assert hand.touching(4, 8)
    assert hand.pinch_center == (51, 41)
    assert hand.palm_center == (43, 55)


def test_face_mouth():
    pts = [(0, 0)] * 292
    pts[13] = (50, 50)
    pts[14] = (50, 70)
    pts[61] = (20, 60)
    pts[291] = (80, 60)
    face = Face(tuple(pts), True, True, False, 0.33)
    assert face.mouth_center == (50, 60)
    assert face.mouth_width == 60
    assert face.near_mouth((53, 63), 5)
    assert not face.near_mouth((150, 150), 5)


def test_load_and_draw_rgba_with_clipping(tmp_path):
    sprite = np.zeros((5, 5, 4), dtype=np.uint8)
    sprite[:, :, :3] = (10, 50, 200)
    sprite[:, :, 3] = 255
    sprite[2, 2, 3] = 0
    png = tmp_path / 'chip.png'
    assert cv2.imwrite(str(png), sprite)
    loaded = load_picture(png, size=(5, 5))
    frame = np.zeros((9, 9, 3), dtype=np.uint8)
    show_picture(frame, loaded, at=(4, 4))
    assert tuple(frame[4, 4]) == (0, 0, 0)  # transparent center
    assert tuple(frame[2, 2]) == (10, 50, 200)
    # Crop safely at corner; no negative-slice wraparound.
    second = np.zeros((9, 9, 3), dtype=np.uint8)
    show_picture(second, loaded, at=(0, 0))
    assert tuple(second[0, 0]) == (0, 0, 0)
    assert tuple(second[1, 1]) == (10, 50, 200)


def test_local_picture_by_path(tmp_path):
    image_path = tmp_path / 'x.png'
    cv2.imwrite(str(image_path), np.ones((2, 2, 3), dtype=np.uint8) * 100)
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    show_picture(frame, str(image_path), at=(2, 2))
    assert (frame[1:3, 1:3] == 100).all()


def test_text_and_dot():
    frame = np.zeros((100, 160, 3), dtype=np.uint8)
    assert show_text(frame, 'test') is frame
    assert show_point(frame, (40, 50)) is frame
    assert frame.sum() > 0


def test_model_paths(tmp_path):
    hand, face = model_paths(tmp_path)
    assert hand.name == 'hand_landmarker.task'
    assert face.name == 'face_landmarker.task'
