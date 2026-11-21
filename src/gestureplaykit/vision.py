"""MediaPipe VIDEO-mode tracking and beginner-friendly gesture events.

Tracking is estimated from a 2-D camera view. It cannot prove physical
contact and should not be used for safety-critical or access-control tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import time
from typing import Sequence

import cv2
import numpy as np

from .models import model_paths
from .pose import Pose

Point = tuple[int, int]
_FINGERS = {
    "thumb": (4, 3),
    "index": (8, 6),
    "middle": (12, 10),
    "ring": (16, 14),
    "pinky": (20, 18),
}


def _distance(a: Sequence[float], b: Sequence[float]) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


def _midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)


@dataclass(frozen=True)
class Hand:
    """One detected hand in the latest frame (landmarks numbered 0..20).

    Event fields (``pinch_started``, ``pinch_ended``, ``double_pinched``) are
    true only in the frame where that event is detected. ``id`` is a best-effort
    tracking ID while the hand stays visible; it isn't biometric identity.
    """

    points: tuple[Point, ...]
    pinching: bool
    pinch_started: bool
    pinch_ended: bool
    double_pinched: bool
    id: int | None = None
    handedness: str | None = None
    handedness_score: float | None = None
    normalized_points: tuple[tuple[float, float, float], ...] = ()
    world_points: tuple[tuple[float, float, float], ...] = ()

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        """Landmark bounding box as (left, top, right, bottom) in pixels."""
        return (min(p[0] for p in self.points), min(p[1] for p in self.points),
                max(p[0] for p in self.points), max(p[1] for p in self.points))

    @property
    def wrist(self) -> Point:
        return self.landmark(0)

    @property
    def thumb_tip(self) -> Point:
        return self.landmark(4)

    @property
    def index_tip(self) -> Point:
        return self.landmark(8)

    @property
    def palm_width(self) -> float:
        return self.distance(5, 17)

    @property
    def pinch_strength(self) -> float:
        """0..1 approximate pinch strength; 1 means fingertips overlap."""
        if self.palm_width == 0:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.distance(4, 8) / self.palm_width))

    @property
    def raised_finger_count(self) -> int:
        return sum(self.fingers_up.values())

    @property
    def peace_sign(self) -> bool:
        f = self.fingers_up
        return f["index"] and f["middle"] and not f["ring"] and not f["pinky"]

    @property
    def pointing(self) -> bool:
        f = self.fingers_up
        return f["index"] and not any(f[x] for x in ("middle", "ring", "pinky"))

    def landmark(self, number: int) -> Point:
        """Get landmark pixel position, e.g. 4=thumb tip and 8=index tip."""
        if not isinstance(number, int) or isinstance(number, bool) or not 0 <= number < 21:
            raise ValueError("Hand landmark number must be an integer from 0 to 20")
        return self.points[number]

    def distance(self, a: int, b: int) -> float:
        """Pixel distance between two landmarks."""
        return _distance(self.landmark(a), self.landmark(b))

    def touching(self, a: int, b: int, ratio: float = 0.35) -> bool:
        """Estimate contact using distance relative to width of the palm."""
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("ratio must be a positive, finite number")
        palm_width = self.distance(5, 17)
        return palm_width > 0 and self.distance(a, b) < palm_width * ratio

    @property
    def pinch_center(self) -> Point:
        """Midpoint between thumb and index fingertips in pixels."""
        return _midpoint(self.landmark(4), self.landmark(8))

    @property
    def palm_center(self) -> Point:
        """Approximate center of the palm in pixels."""
        points = [self.landmark(i) for i in (0, 5, 9, 13, 17)]
        return (sum(p[0] for p in points) // len(points),
                sum(p[1] for p in points) // len(points))

    def finger_up(self, finger: str) -> bool:
        """Estimate whether a finger is extended from its 2-D landmarks.

        Best with a mostly front-facing hand. For thumb, we compare distances
        from the pinky base; for other fingers, distances from the wrist.
        """
        key = finger.strip().lower()
        if key not in _FINGERS:
            raise ValueError(f"finger must be one of: {', '.join(_FINGERS)}")
        tip, middle_joint = _FINGERS[key]
        anchor = 17 if key == "thumb" else 0
        return self.distance(tip, anchor) > self.distance(middle_joint, anchor) * 1.08

    @property
    def fingers_up(self) -> dict[str, bool]:
        """Estimates for thumb, index, middle, ring and pinky extension."""
        return {finger: self.finger_up(finger) for finger in _FINGERS}

    @property
    def open_palm(self) -> bool:
        """Estimate an open hand (the four non-thumb fingers are extended)."""
        return all(self.finger_up(finger) for finger in ("index", "middle", "ring", "pinky"))

    @property
    def fist(self) -> bool:
        """Estimate a fist (the four non-thumb fingers are folded)."""
        return not any(self.finger_up(finger) for finger in ("index", "middle", "ring", "pinky"))


@dataclass(frozen=True)
class Face:
    """One tracked face; mouth state is estimated from facial landmarks."""

    points: tuple[Point, ...]
    mouth_open: bool
    mouth_just_opened: bool
    mouth_just_closed: bool
    mouth_ratio: float
    blendshapes: dict[str, float] | None = None
    transformation_matrix: tuple[tuple[float, ...], ...] | None = None
    normalized_points: tuple[tuple[float, float, float], ...] = ()
    blink_started: bool = False
    blink_ended: bool = False

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        return (min(x for x, _ in self.points), min(y for _, y in self.points),
                max(x for x, _ in self.points), max(y for _, y in self.points))

    @property
    def face_center(self) -> Point:
        x1, y1, x2, y2 = self.bounding_box
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def nose_tip(self) -> Point:
        return self.landmark(1)

    @property
    def chin(self) -> Point:
        return self.landmark(152)

    @property
    def forehead(self) -> Point:
        return self.landmark(10)

    @property
    def mouth_height(self) -> float:
        return _distance(self.landmark(13), self.landmark(14))

    @property
    def left_eye_center(self) -> Point:
        return _midpoint(self.landmark(33), self.landmark(133))

    @property
    def right_eye_center(self) -> Point:
        return _midpoint(self.landmark(362), self.landmark(263))

    def eye_open_ratio(self, side: str) -> float:
        """Approximate eyelid gap / eye width (not a medical measurement)."""
        if side.lower() == "left":
            a, b, upper, lower = 33, 133, 159, 145
        elif side.lower() == "right":
            a, b, upper, lower = 362, 263, 386, 374
        else:
            raise ValueError("side must be 'left' or 'right'")
        width = _distance(self.landmark(a), self.landmark(b))
        return _distance(self.landmark(upper), self.landmark(lower)) / width if width else 0.0

    def expression(self, name: str, default: float = 0.0) -> float:
        """Read a MediaPipe blendshape by name, e.g. 'jawOpen' or 'mouthSmileLeft'."""
        return (self.blendshapes or {}).get(name, default)

    @property
    def smiling(self) -> bool:
        """Smile estimate from the two model blendshape scores."""
        return (self.expression("mouthSmileLeft") + self.expression("mouthSmileRight")) / 2 >= 0.45

    @property
    def left_eye_closed(self) -> bool:
        return self.expression("eyeBlinkLeft") >= 0.55

    @property
    def right_eye_closed(self) -> bool:
        return self.expression("eyeBlinkRight") >= 0.55

    @property
    def eyes_closed(self) -> bool:
        return self.left_eye_closed and self.right_eye_closed

    @property
    def winking(self) -> bool:
        return self.left_eye_closed != self.right_eye_closed

    @property
    def mouth_closed(self) -> bool:
        return not self.mouth_open

    def distance(self, a: int, b: int) -> float:
        return _distance(self.landmark(a), self.landmark(b))

    def landmark(self, number: int) -> Point:
        if not isinstance(number, int) or isinstance(number, bool) or not 0 <= number < len(self.points):
            raise ValueError(f"Face landmark number must be 0..{len(self.points)-1}")
        return self.points[number]

    @property
    def mouth_center(self) -> Point:
        return _midpoint(self.landmark(13), self.landmark(14))

    @property
    def mouth_width(self) -> float:
        return _distance(self.landmark(61), self.landmark(291))

    def near_mouth(self, position: Sequence[float], max_distance: float = 70) -> bool:
        """Check whether a screen point lies near the mouth's approximate center."""
        if not math.isfinite(max_distance) or max_distance < 0:
            raise ValueError("max_distance must be nonnegative and finite")
        return _distance(self.mouth_center, position) <= max_distance


class Vision:
    """Track hands and/or a face from individual OpenCV BGR video frames.

    Download models separately with ``download_models()`` once. ``vision.hands``
    includes all hands; ``vision.hand`` is the first or ``None``. Gesture events
    are not persistent flags: read them on every ``vision.update(frame)``.
    """

    def __init__(self, models_dir="models", hands=True, faces=True,
                 max_hands=2, pinch_start=0.35, pinch_release=0.50,
                 double_pinch_window=0.60, mouth_open_ratio=0.20,
                 mouth_closed_ratio=0.12, poses=False, max_poses=1,
                 face_blendshapes=True, face_transformations=False):
        self.models_dir = Path(models_dir).expanduser()
        self.detect_hands = bool(hands)
        self.detect_faces = bool(faces)
        self.detect_poses = bool(poses)
        self.face_blendshapes = bool(face_blendshapes)
        self.face_transformations = bool(face_transformations)
        if not self.detect_hands and not self.detect_faces and not self.detect_poses:
            raise ValueError("Enable hand, face and/or pose tracking")
        if not isinstance(max_poses, int) or isinstance(max_poses, bool) or max_poses < 1:
            raise ValueError("max_poses must be a positive integer")
        self.max_poses = max_poses
        if not isinstance(max_hands, int) or isinstance(max_hands, bool) or max_hands < 1:
            raise ValueError("max_hands must be a positive integer")
        for name, value in (
            ("pinch_start", pinch_start), ("pinch_release", pinch_release),
            ("mouth_open_ratio", mouth_open_ratio), ("mouth_closed_ratio", mouth_closed_ratio),
        ):
            if not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        if pinch_start >= pinch_release:
            raise ValueError("pinch_start must be smaller than pinch_release")
        if mouth_closed_ratio >= mouth_open_ratio:
            raise ValueError("mouth_closed_ratio must be smaller than mouth_open_ratio")
        if not isinstance(double_pinch_window, (int, float)) or not math.isfinite(double_pinch_window) or double_pinch_window <= 0.08:
            raise ValueError("double_pinch_window must be greater than 0.08 seconds")
        self.max_hands = max_hands
        self.pinch_start = float(pinch_start)
        self.pinch_release = float(pinch_release)
        self.double_pinch_window = float(double_pinch_window)
        self.mouth_open_ratio = float(mouth_open_ratio)
        self.mouth_closed_ratio = float(mouth_closed_ratio)
        self.hands: list[Hand] = []
        self.hand: Hand | None = None
        self.face: Face | None = None
        self.poses: list[Pose] = []
        self.pose: Pose | None = None
        self._poses_tracker = None
        self._blink_was_closed = False
        self._hands_tracker = None
        self._faces_tracker = None
        self._hand_history: dict[int, dict] = {}
        self._next_hand_id = 0
        self._face_open_before = False
        self._start: float | None = None
        self._last_timestamp = -1

    def __enter__(self) -> "Vision":
        if self._start is not None:
            raise RuntimeError("Vision is already started")
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError("MediaPipe not installed; run: python -m pip install gestureplaykit") from exc
        hand_path, face_path = model_paths(self.models_dir)
        from .models import pose_model_path
        body_path = pose_model_path(self.models_dir)
        for enabled, path in ((self.detect_hands, hand_path), (self.detect_faces, face_path),
                              (self.detect_poses, body_path)):
            if enabled and not path.is_file():
                raise FileNotFoundError(
                    f"Model not found: {path}. Run: python -m gestureplaykit download-models"
                )
        self._mp = mp
        mode = mp.tasks.vision.RunningMode.VIDEO
        try:
            if self.detect_hands:
                options = mp.tasks.vision.HandLandmarkerOptions(
                    base_options=mp.tasks.BaseOptions(model_asset_path=str(hand_path)),
                    running_mode=mode, num_hands=self.max_hands)
                self._hands_tracker = mp.tasks.vision.HandLandmarker.create_from_options(options)
            if self.detect_faces:
                options = mp.tasks.vision.FaceLandmarkerOptions(
                    base_options=mp.tasks.BaseOptions(model_asset_path=str(face_path)),
                    running_mode=mode, num_faces=1,
                    output_face_blendshapes=self.face_blendshapes,
                    output_facial_transformation_matrixes=self.face_transformations)
                self._faces_tracker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
            if self.detect_poses:
                options = mp.tasks.vision.PoseLandmarkerOptions(
                    base_options=mp.tasks.BaseOptions(model_asset_path=str(body_path)),
                    running_mode=mode, num_poses=self.max_poses)
                self._poses_tracker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        except Exception:
            self.close()
            raise
        self.reset()
        self._start = time.monotonic()
        return self

    def reset(self) -> None:
        """Forget gesture history; useful when changing scenes or restarting."""
        self.hands = []
        self.hand = None
        self.face = None
        self.poses = []
        self.pose = None
        self._blink_was_closed = False
        self._hand_history.clear()
        self._next_hand_id = 0
        self._face_open_before = False
        self._last_timestamp = -1

    def _match_hands(self, detected: list[tuple[Point, ...]]) -> list[int]:
        """Associate hands with previous frames by nearest palm center.

        IDs are best-effort only; hands crossing/occluding may still swap IDs.
        """
        candidates = []
        centers = []
        widths = []
        for points in detected:
            center = (sum(points[i][0] for i in (0, 5, 9, 13, 17)) // 5,
                      sum(points[i][1] for i in (0, 5, 9, 13, 17)) // 5)
            centers.append(center)
            widths.append(_distance(points[5], points[17]))
        for index, center in enumerate(centers):
            for hand_id, history in self._hand_history.items():
                limit = max(30.0, 1.8 * max(widths[index], history["width"]))
                dist = _distance(center, history["center"])
                if dist <= limit:
                    candidates.append((dist, index, hand_id))
        matched = {}
        taken = set()
        for _dist, index, hand_id in sorted(candidates):
            if index not in matched and hand_id not in taken:
                matched[index] = hand_id
                taken.add(hand_id)
        for index in range(len(detected)):
            if index not in matched:
                matched[index] = self._next_hand_id
                self._next_hand_id += 1
        return [matched[i] for i in range(len(detected))]

    def update(self, frame: np.ndarray) -> "Vision":
        """Process one BGR ``uint8`` frame; returns ``self`` for convenience."""
        if self._start is None:
            raise RuntimeError("Vision not started; use 'with Vision() as vision:'.")
        if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
            raise ValueError("frame must be a H×W×3 uint8 BGR NumPy array")
        height, width = frame.shape[:2]
        if width < 1 or height < 1:
            raise ValueError("frame must not be empty")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        now = time.monotonic()
        timestamp = max(self._last_timestamp + 1, int((now - self._start) * 1000))
        self._last_timestamp = timestamp

        self.hands = []
        if self._hands_tracker is not None:
            result = self._hands_tracker.detect_for_video(image, timestamp)
            detected = [tuple((round(p.x * width), round(p.y * height)) for p in landmarks)
                        for landmarks in result.hand_landmarks]
            hand_ids = self._match_hands(detected)
            current_history = {}
            for points, hand_id in zip(detected, hand_ids):
                previous = self._hand_history.get(hand_id, {"down": False, "last_start": -100.0})
                palm_width = _distance(points[5], points[17])
                threshold = self.pinch_release if previous["down"] else self.pinch_start
                down = palm_width > 0 and _distance(points[4], points[8]) < palm_width * threshold
                started = down and not previous["down"]
                ended = not down and previous["down"]
                double = False
                last_start = previous["last_start"]
                if started:
                    gap = now - last_start
                    double = 0.08 <= gap <= self.double_pinch_window
                    last_start = -100.0 if double else now
                center = (sum(points[i][0] for i in (0, 5, 9, 13, 17)) // 5,
                          sum(points[i][1] for i in (0, 5, 9, 13, 17)) // 5)
                current_history[hand_id] = {
                    "down": down, "last_start": last_start, "center": center,
                    "width": palm_width,
                }
                idx = len(self.hands)
                label, confidence = None, None
                if idx < len(getattr(result, "handedness", [])) and result.handedness[idx]:
                    category = result.handedness[idx][0]
                    label = getattr(category, "category_name", None)
                    confidence = getattr(category, "score", None)
                raw = result.hand_landmarks[idx]
                raw_xyz = tuple((float(p.x), float(p.y), float(getattr(p, "z", 0.0))) for p in raw)
                world = getattr(result, "hand_world_landmarks", [])
                world_xyz = (tuple((float(p.x), float(p.y), float(getattr(p, "z", 0.0))) for p in world[idx])
                             if idx < len(world) else ())
                self.hands.append(Hand(points, down, started, ended, double, id=hand_id,
                                       handedness=label, handedness_score=confidence,
                                       normalized_points=raw_xyz, world_points=world_xyz))
            # Drop missing hands and their gesture history to prevent false events.
            self._hand_history = current_history
        self.hand = self.hands[0] if self.hands else None

        self.face = None
        if self._faces_tracker is not None:
            result = self._faces_tracker.detect_for_video(image, timestamp)
            if result.face_landmarks:
                points = tuple((round(p.x * width), round(p.y * height))
                               for p in result.face_landmarks[0])
                width_px = _distance(points[61], points[291])
                ratio = _distance(points[13], points[14]) / width_px if width_px > 0 else 0.0
                is_open = self._face_open_before
                if ratio >= self.mouth_open_ratio:
                    is_open = True
                elif ratio <= self.mouth_closed_ratio:
                    is_open = False
                shapes = {}
                groups = getattr(result, "face_blendshapes", []) or []
                if groups:
                    shapes = {str(c.category_name): float(c.score) for c in groups[0]}
                transforms = getattr(result, "facial_transformation_matrixes", []) or []
                matrix = None
                if len(transforms):
                    matrix = tuple(tuple(float(v) for v in row) for row in np.asarray(transforms[0]))
                blink_now = (shapes.get("eyeBlinkLeft", 0) >= 0.55 and
                             shapes.get("eyeBlinkRight", 0) >= 0.55)
                raw_points = tuple((float(p.x), float(p.y), float(getattr(p, "z", 0.0)))
                                   for p in result.face_landmarks[0])
                self.face = Face(points, is_open, is_open and not self._face_open_before,
                                 not is_open and self._face_open_before, ratio,
                                 blendshapes=shapes, transformation_matrix=matrix,
                                 normalized_points=raw_points,
                                 blink_started=blink_now and not self._blink_was_closed,
                                 blink_ended=not blink_now and self._blink_was_closed)
                self._blink_was_closed = blink_now
                self._face_open_before = is_open
            else:
                self._face_open_before = False
                self._blink_was_closed = False
        self.poses = []
        if self._poses_tracker is not None:
            result = self._poses_tracker.detect_for_video(image, timestamp)
            for index, landmarks in enumerate(result.pose_landmarks):
                points = tuple((round(p.x * width), round(p.y * height)) for p in landmarks)
                raw_points = tuple((float(p.x), float(p.y), float(getattr(p, "z", 0.0))) for p in landmarks)
                world = getattr(result, "pose_world_landmarks", []) or []
                world_xyz = (tuple((float(p.x), float(p.y), float(getattr(p, "z", 0.0))) for p in world[index])
                             if index < len(world) else ())
                visibilities = tuple(float(getattr(p, "visibility", 1.0) or 0.0) for p in landmarks)
                self.poses.append(Pose(points, normalized_points=raw_points,
                                       world_points=world_xyz, visibilities=visibilities))
        self.pose = self.poses[0] if self.poses else None
        return self

    def close(self) -> None:
        """Close model trackers and release their resources (safe to call twice)."""
        for name in ("_hands_tracker", "_faces_tracker", "_poses_tracker"):
            tracker = getattr(self, name)
            if tracker is not None:
                tracker.close()
                setattr(self, name, None)
        self._start = None
        self.reset()

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
