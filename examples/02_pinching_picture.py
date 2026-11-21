"""When you pinch, display a chip between your fingertips."""
from pathlib import Path
from gestureplaykit import Camera, Vision, load_picture, show_picture, show_text

# Replace with any PNG you want. You can use a direct HTTPS image URL too.
IMAGE = Path(__file__).resolve().parent / "chip.png"

# Run `download_models('models')` once before using Vision().
chip = load_picture(IMAGE, size=(110, 110))

with Camera() as camera, Vision(models_dir="models", faces=False) as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        if vision.hand and vision.hand.pinching:
            show_picture(frame, chip, at=vision.hand.pinch_center)
        show_text(frame, "Pinch your fingers to show the chip. Q to quit.")
        if not camera.show(frame, title="My Pinch Project"):
            break
