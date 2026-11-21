"""Load pictures and draw overlays on OpenCV BGR webcam frames.

Colors use OpenCV BGR order (blue, green, red). Unlike game engines,
functions modify the supplied frame in place and also return it.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import math

import cv2
import numpy as np

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000

# MediaPipe's 21-hand-landmark skeleton, used only for drawing.
_HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)


def _image_ok(image: np.ndarray, name: str) -> None:
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
            or image.ndim != 3 or image.shape[2] not in (3, 4)
            or image.shape[0] == 0 or image.shape[1] == 0):
        raise ValueError(f"{name} must be a nonempty uint8 BGR or BGRA NumPy array")
    if image.shape[0] * image.shape[1] > MAX_IMAGE_PIXELS:
        raise ValueError(f"{name} is too large (maximum {MAX_IMAGE_PIXELS:,} pixels)")


def _validate_size(size) -> tuple[int, int]:
    try:
        if len(size) != 2:
            raise ValueError
        width, height = size
        if isinstance(width, bool) or isinstance(height, bool):
            raise ValueError
        width, height = int(width), int(height)
    except (ValueError, TypeError) as exc:
        raise ValueError("size must be (width, height) with positive integers") from exc
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise ValueError("size must be positive and at most 40 million pixels")
    return width, height


@lru_cache(maxsize=32)
def _load_source(source: str) -> np.ndarray:
    """Decode an image once; callers get their own copy."""
    parsed = urlsplit(source)
    if parsed.scheme.lower() in {"https", "http"}:
        request = Request(source, headers={"User-Agent": "GesturePlayKit/1.0"})
        with urlopen(request, timeout=15) as response:
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Image download is too large (>15 MB)")
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    else:
        path = Path(source).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Picture not found: {path}")
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image file is too large (>15 MB)")
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Picture can't be decoded: {source}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    _image_ok(image, "picture")
    return image


def load_picture(source: str | Path, size=None) -> np.ndarray:
    """Read a PNG/JPG from local path or direct HTTP(S) image URL.

    Call before the camera loop whenever possible; decoding and URL downloads
    are cached. The returned image is a fresh copy you can modify.
    """
    image = _load_source(str(source)).copy()
    return resize_picture(image, size) if size is not None else image


def resize_picture(picture: np.ndarray, size) -> np.ndarray:
    """Resize an existing image using a high-quality interpolation choice."""
    _image_ok(picture, "picture")
    width, height = _validate_size(size)
    interpolation = cv2.INTER_AREA if width < picture.shape[1] or height < picture.shape[0] else cv2.INTER_LINEAR
    return cv2.resize(picture, (width, height), interpolation=interpolation)


# One process-wide display switch for picture overlays. Shape/text rendering is unaffected.
# This controls future show_picture() calls; pixels already drawn cannot be undone.
_PICTURES_VISIBLE = True


def pictures_visible() -> bool:
    """Return whether picture overlays are enabled (on by default)."""
    return _PICTURES_VISIBLE


def set_pictures_visible(visible: bool) -> None:
    """Enable or disable overlays drawn by :func:`show_picture`.

    This is a process-wide setting, intended for one game or display loop.
    It does not hide webcam video, text, hand landmarks, or previously drawn
    pixels on the same frame. Read a fresh frame to clear old overlays.
    """
    if not isinstance(visible, bool):
        raise TypeError("visible must be True or False")
    global _PICTURES_VISIBLE
    _PICTURES_VISIBLE = visible


def hide_all_pictures() -> None:
    """Skip all future :func:`show_picture` overlays until re-enabled."""
    set_pictures_visible(False)


def show_all_pictures() -> None:
    """Re-enable picture overlays (the default)."""
    set_pictures_visible(True)


def toggle_pictures() -> bool:
    """Flip overlay visibility and return the new visible state."""
    set_pictures_visible(not pictures_visible())
    return pictures_visible()


def show_picture(frame: np.ndarray, picture: np.ndarray | str | Path,
                 at, size=None, opacity: float = 1.0) -> np.ndarray:
    """Overlay a picture centered at pixel coordinate ``at=(x,y)``.

    Supports BGRA transparency, optional resizing and opacity (0..1). Clips
    safely when the picture overlaps the edge. Mutates and returns ``frame``.
    If pictures are hidden, leaves ``frame`` unchanged without loading assets.
    """
    _image_ok(frame, "frame")
    if frame.shape[2] != 3:
        raise ValueError("frame must be a 3-channel BGR image")
    if not isinstance(opacity, (int, float)) or not math.isfinite(opacity) or not 0 <= opacity <= 1:
        raise ValueError("opacity must be a number from 0 to 1")
    if not _PICTURES_VISIBLE:
        return frame
    if isinstance(picture, (str, Path)):
        picture = load_picture(picture, size=size)
    elif size is not None:
        picture = resize_picture(picture, size)
    _image_ok(picture, "picture")
    if opacity == 0:
        return frame

    h, w = picture.shape[:2]
    frame_h, frame_w = frame.shape[:2]
    left_at, top_at = int(at[0]) - w // 2, int(at[1]) - h // 2
    x1, y1 = max(0, left_at), max(0, top_at)
    x2, y2 = min(frame_w, left_at + w), min(frame_h, top_at + h)
    if x1 >= x2 or y1 >= y2:
        return frame

    foreground = picture[y1-top_at:y2-top_at, x1-left_at:x2-left_at]
    background = frame[y1:y2, x1:x2]
    if foreground.shape[2] == 4:
        a = (foreground[:, :, 3:4].astype(np.float32) / 255.0) * opacity
    else:
        a = opacity
    if isinstance(a, float) and a == 1.0:
        background[:] = foreground[:, :, :3]
    else:
        background[:] = (a * foreground[:, :, :3].astype(np.float32)
                         + (1-a) * background.astype(np.float32)).astype(np.uint8)
    return frame


def show_text(frame, text, at=(15, 35), color=(255, 255, 255),
              scale=0.7, thickness=2):
    """Draw text at a pixel position, in BGR color order."""
    cv2.putText(frame, str(text), tuple(map(int, at)), cv2.FONT_HERSHEY_SIMPLEX,
                float(scale), tuple(map(int, color)), int(thickness), cv2.LINE_AA)
    return frame


def show_point(frame, at, color=(0, 255, 255), radius=7):
    """Draw a filled circle at a point, useful for landmark visualizations."""
    cv2.circle(frame, tuple(map(int, at)), int(radius), tuple(map(int, color)), -1)
    return frame


def show_line(frame, start, end, color=(255, 255, 255), thickness=2):
    """Draw a line between two screen coordinates."""
    cv2.line(frame, tuple(map(int, start)), tuple(map(int, end)),
             tuple(map(int, color)), int(thickness), cv2.LINE_AA)
    return frame


def show_rectangle(frame, rect, color=(255, 255, 255), thickness=2, fill=False):
    """Draw a rectangle given (left, top, right, bottom)."""
    if len(rect) != 4:
        raise ValueError("rect must be (left, top, right, bottom)")
    cv2.rectangle(frame, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])),
                  tuple(map(int, color)), -1 if fill else int(thickness))
    return frame


def draw_hand(frame, hand, color=(0, 255, 255),
              number_landmarks=False, radius=4):
    """Draw the 21 hand landmarks and skeleton onto a BGR frame.

    Accepts a ``Hand`` object from Vision or a sequence of 21 point tuples.
    """
    points = hand.points if hasattr(hand, "points") else hand
    if len(points) != 21:
        raise ValueError("draw_hand expects 21 landmark points")
    for a, b in _HAND_CONNECTIONS:
        show_line(frame, points[a], points[b], color=color, thickness=2)
    for i, point in enumerate(points):
        show_point(frame, point, color=color, radius=radius)
        if number_landmarks:
            show_text(frame, i, at=(point[0] + 5, point[1] - 5), color=color,
                      scale=0.4, thickness=1)
    return frame
