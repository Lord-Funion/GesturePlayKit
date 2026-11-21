"""Show a semitransparent image centered on a fingertip pinch."""
from pathlib import Path
from gestureplaykit import Camera, Vision, load_picture, show_picture, show_text

chip = load_picture(Path(__file__).with_name("chip.png"), size=(110, 110))

with Camera() as camera, Vision(models_dir="models", faces=False) as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        for hand in vision.hands:
            if hand.pinching:
                show_picture(frame, chip, hand.pinch_center, opacity=0.75)
                show_text(frame, "Pinching!", at=(15, 70))
        if not camera.show(frame, title="Picture overlay demo"):
            break
