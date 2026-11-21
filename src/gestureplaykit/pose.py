"""Simple body tracking: MediaPipe Pose's 33 landmarks and useful gestures.

This is approximate computer vision, not a medical or biomechanics tool.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

Point = tuple[int, int]

POSE_LANDMARKS = {
    "nose": 0, "left_eye_inner": 1, "left_eye": 2,
    "left_eye_outer": 3, "right_eye_inner": 4, "right_eye": 5,
    "right_eye_outer": 6, "left_ear": 7, "right_ear": 8,
    "mouth_left": 9, "mouth_right": 10,
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_pinky": 17, "right_pinky": 18,
    "left_index": 19, "right_index": 20,
    "left_thumb": 21, "right_thumb": 22,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
    "left_heel": 29, "right_heel": 30,
    "left_foot_index": 31, "right_foot_index": 32,
}

# Common visual skeleton; deliberately no connections across the face.
POSE_CONNECTIONS = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32),
)


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle(a: Point, b: Point, c: Point) -> float:
    """Angle ABC in degrees, 0..180; returns 0 for degenerate segments."""
    ux, uy = a[0] - b[0], a[1] - b[1]
    vx, vy = c[0] - b[0], c[1] - b[1]
    norm = math.hypot(ux, uy) * math.hypot(vx, vy)
    if norm < 1e-9:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, (ux * vx + uy * vy) / norm))))


@dataclass(frozen=True)
class Pose:
    """Detected body with 33 2D joints and optional model 3D outputs.

    Coordinates are in webcam pixels. world_points are model estimates and do
    not replace calibrated motion capture. If a joint is occluded, positions
    and calculated angles may be unreliable; inspect visibility first.
    """

    points: tuple[Point, ...]
    normalized_points: tuple[tuple[float, float, float], ...] = ()
    world_points: tuple[tuple[float, float, float], ...] = ()
    visibilities: tuple[float, ...] = ()

    def landmark(self, number: int | str) -> Point:
        if isinstance(number, str):
            if number not in POSE_LANDMARKS:
                raise ValueError(f"Unknown body landmark: {number}")
            number = POSE_LANDMARKS[number]
        if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number < 33:
            raise ValueError("Pose landmark must be an index 0..32 or known name")
        return self.points[number]

    def visibility(self, number: int | str) -> float:
        index = POSE_LANDMARKS[number] if isinstance(number, str) else number
        self.landmark(index)
        return self.visibilities[index] if self.visibilities else 1.0

    def distance(self, a: int | str, b: int | str) -> float:
        return _distance(self.landmark(a), self.landmark(b))

    def angle(self, a: int | str, center: int | str, c: int | str) -> float:
        return _angle(self.landmark(a), self.landmark(center), self.landmark(c))

    @property
    def left_elbow_angle(self) -> float:
        return self.angle("left_shoulder", "left_elbow", "left_wrist")

    @property
    def right_elbow_angle(self) -> float:
        return self.angle("right_shoulder", "right_elbow", "right_wrist")

    @property
    def left_knee_angle(self) -> float:
        return self.angle("left_hip", "left_knee", "left_ankle")

    @property
    def right_knee_angle(self) -> float:
        return self.angle("right_hip", "right_knee", "right_ankle")

    @property
    def shoulders_center(self) -> Point:
        a, b = self.landmark("left_shoulder"), self.landmark("right_shoulder")
        return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)

    @property
    def hips_center(self) -> Point:
        a, b = self.landmark("left_hip"), self.landmark("right_hip")
        return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)

    @property
    def arms_raised(self) -> bool:
        """Are both wrists above their respective shoulders in the image?"""
        return (self.landmark("left_wrist")[1] < self.landmark("left_shoulder")[1]
                and self.landmark("right_wrist")[1] < self.landmark("right_shoulder")[1])

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        return (min(p[0] for p in self.points), min(p[1] for p in self.points),
                max(p[0] for p in self.points), max(p[1] for p in self.points))


def draw_pose(frame, pose: Pose, *, color=(90, 245, 90), radius=4,
              number_landmarks=False, minimum_visibility=0.4):
    """Draw body skeleton, optionally showing each landmark's number."""
    import cv2
    for a, b in POSE_CONNECTIONS:
        if pose.visibility(a) >= minimum_visibility and pose.visibility(b) >= minimum_visibility:
            cv2.line(frame, pose.points[a], pose.points[b], color, 2, cv2.LINE_AA)
    for i, point in enumerate(pose.points):
        if pose.visibility(i) < minimum_visibility:
            continue
        cv2.circle(frame, point, radius, color, -1)
        if number_landmarks:
            cv2.putText(frame, str(i), (point[0]+4, point[1]-4),
                        cv2.FONT_HERSHEY_SIMPLEX, .35, color, 1, cv2.LINE_AA)
    return frame
