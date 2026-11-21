"""Simple webcam capture and window display."""

import cv2


class Camera:
    """Read webcam frames and show them in a window.

    Example::

        with Camera() as camera:
            while (frame := camera.read()) is not None:
                if not camera.show(frame):
                    break

    On Windows, camera indices may be 0, 1, 2, etc.
    """

    def __init__(self, index: int = 0, width: int = 640, height: int = 480,
                 mirror: bool = True):
        self.index = index
        self.width = width
        self.height = height
        self.mirror = mirror
        self._capture = None

    def __enter__(self):
        self._capture = cv2.VideoCapture(self.index)
        if not self._capture.isOpened():
            self._capture.release()
            self._capture = None
            raise RuntimeError(f"Couldn't open camera {self.index}; check permissions or other apps.")
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self

    def read(self):
        """Return a BGR image (NumPy array) or None when the webcam stops."""
        if self._capture is None:
            raise RuntimeError("Camera is not open. Use 'with Camera() as camera:'.")
        ok, frame = self._capture.read()
        if not ok:
            return None
        return cv2.flip(frame, 1) if self.mirror else frame

    def show(self, frame, title: str = "GesturePlayKit", quit_key: str = "q") -> bool:
        """Display frame; return False if Q/quit_key or Escape is pressed."""
        if not isinstance(quit_key, str) or len(quit_key) != 1:
            raise ValueError("quit_key must be a single character")
        cv2.imshow(title, frame)
        key = cv2.waitKey(1) & 0xFF
        return key not in (ord(quit_key.lower()), 27)

    def close(self):
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        cv2.destroyAllWindows()

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
