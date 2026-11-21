"""Explore all 21 hand landmarks and their coordinates."""
from gestureplaykit import Camera, Vision, show_point, show_text

with Camera() as camera, Vision(models_dir="models", faces=False) as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        if vision.hand:
            for number in range(21):
                point = vision.hand.landmark(number)
                show_point(frame, point, radius=3)
                show_text(frame, str(number), (point[0] + 5, point[1] - 5), scale=0.35)
            show_point(frame, vision.hand.palm_center, color=(255, 0, 255), radius=8)
        if not camera.show(frame, title="Hand Landmarks"):
            break
