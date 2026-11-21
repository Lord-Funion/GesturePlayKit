"""Extended v1.1 tracking semantics and public API without a physical webcam."""
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from gestureplaykit import Face, Hand, Pose, Vision, draw_pose
from gestureplaykit.models import pose_model_path
from gestureplaykit.pose import POSE_LANDMARKS


def face_points():
    pts = [(50, 50)] * 478
    pts[13], pts[14], pts[61], pts[291] = (50, 49), (50, 59), (30, 53), (70, 53)
    pts[33], pts[133], pts[159], pts[145] = (30, 30), (42, 30), (35, 26), (35, 33)
    pts[362], pts[263], pts[386], pts[374] = (58, 30), (70, 30), (65, 26), (65, 33)
    return tuple(pts)


def test_face_all_helpers():
    f = Face(face_points(), True, True, False, .25,
             blendshapes={'eyeBlinkLeft':.95, 'eyeBlinkRight':.1,
                          'mouthSmileLeft':.8, 'mouthSmileRight':.7, 'jawOpen':.4})
    assert f.mouth_open and not f.mouth_closed and f.mouth_height == 10
    assert f.mouth_width == 40 and f.mouth_center == (50, 54)
    assert f.smiling and f.winking and f.left_eye_closed and not f.right_eye_closed
    assert not f.eyes_closed
    assert f.expression('jawOpen') == .4 and f.expression('missing') == 0
    assert f.distance(13, 14) == 10
    assert f.eye_open_ratio('left') > .5
    assert f.left_eye_center == (36, 30)
    assert f.nose_tip == f.landmark(1) and f.forehead == f.landmark(10)
    assert f.face_center == (50, 42)
    assert f.near_mouth((50, 50), max_distance=8)
    assert not f.near_mouth((100, 100), max_distance=5)
    with pytest.raises(ValueError):
        f.eye_open_ratio('center')


def test_hand_extended_helpers():
    pts = [(50, 50)] * 21
    pts[4] = (30, 30)
    pts[8] = (33, 30)
    pts[5], pts[17] = (20, 50), (70, 50)
    pts[0] = (45, 70)
    h = Hand(tuple(pts), True, True, False, False,
             handedness='Right', handedness_score=.95)
    assert h.handedness == 'Right' and h.handedness_score == .95
    assert h.wrist == (45, 70) and h.thumb_tip == (30, 30)
    assert h.palm_width == 50 and .9 < h.pinch_strength < 1
    assert h.bounding_box == (20, 30, 70, 70)
    assert isinstance(h.fingers_up, dict) and isinstance(h.raised_finger_count, int)
    assert isinstance(h.peace_sign, bool) and isinstance(h.pointing, bool)


def pose_points():
    pts = [(100, 100)] * 33
    pts[11], pts[12] = (70, 110), (130, 110)
    pts[13], pts[14] = (70, 90), (130, 90)
    pts[15], pts[16] = (70, 50), (130, 50)
    pts[23], pts[24] = (80, 170), (120, 170)
    pts[25], pts[26] = (80, 210), (120, 210)
    pts[27], pts[28] = (80, 250), (120, 250)
    return tuple(pts)


def test_pose_public_api():
    p = Pose(pose_points(), visibilities=(.98,) * 33)
    assert p.arms_raised
    assert p.landmark('left_wrist') == p.landmark(POSE_LANDMARKS['left_wrist'])
    assert p.distance('left_shoulder', 'right_shoulder') == 60
    assert p.left_elbow_angle == pytest.approx(180)
    assert p.left_knee_angle == pytest.approx(180)
    assert p.shoulders_center == (100, 110)
    assert p.hips_center == (100, 170)
    assert p.visibility('nose') == .98
    canvas = np.zeros((300, 300, 3), dtype=np.uint8)
    assert draw_pose(canvas, p, number_landmarks=True) is canvas
    assert canvas.any()
    with pytest.raises(ValueError):
        p.landmark('shoulder')
    with pytest.raises(ValueError):
        p.landmark(33)


def test_vision_pose_update_using_fake_tracker(monkeypatch):
    class FakeImage:
        def __init__(self, **kwargs):
            pass

    class FakeTracker:
        def detect_for_video(self, img, timestamp):
            raw = [SimpleNamespace(x=x/300, y=y/300, z=0.0, visibility=.9)
                   for x,y in pose_points()]
            return SimpleNamespace(pose_landmarks=[raw], pose_world_landmarks=[])
        def close(self):
            pass

    v = Vision(hands=False, faces=False, poses=True)
    v._start = 0
    v._mp = SimpleNamespace(Image=FakeImage, ImageFormat=SimpleNamespace(SRGB=1))
    v._poses_tracker = FakeTracker()
    monkeypatch.setattr('gestureplaykit.vision.time.monotonic', lambda: 1.0)
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    assert v.update(image) is v
    assert v.pose is v.poses[0]
    assert v.pose.arms_raised
    assert pose_model_path('/tmp/models') == Path('/tmp/models/pose_landmarker_lite.task')
    v.close()
    assert v.pose is None and not v.poses


def test_vision_validation_options():
    with pytest.raises(ValueError):
        Vision(hands=False, faces=False, poses=False)
    with pytest.raises(ValueError):
        Vision(max_poses=0)


def test_pose_model_selector_from_cli(monkeypatch, capsys):
    from gestureplaykit.__main__ import main
    args = []
    monkeypatch.setattr('gestureplaykit.__main__.download_models',
                        lambda path, **kwargs: args.append(kwargs) or (Path('pose.task'),))
    assert main(['download-models', '--poses-only']) == 0
    assert args == [dict(overwrite=False, hands=False, faces=False, poses=True)]
    assert 'pose.task' in capsys.readouterr().out
