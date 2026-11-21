"""Just show a webcam feed. Press Q or Escape to quit."""
from gestureplaykit import Camera, show_text

with Camera() as camera:
    while True:
        frame = camera.read()
        if frame is None:
            break
        show_text(frame, "Hello from GesturePlayKit!")
        if not camera.show(frame):
            break
