"""Double pinch to hide/show every picture overlay. Q or Escape to quit.

Run from the repository root after downloading hand/face models.
"""
from pathlib import Path

from gestureplaykit import (
    Camera, Vision, hide_all_pictures, load_picture, pictures_visible,
    show_picture, show_text, toggle_pictures,
)

chip = load_picture(Path(__file__).with_name("chip.png"), size=(90, 90))

with Camera() as camera, Vision() as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)

        hand = vision.hand
        if hand and hand.double_pinched:
            toggle_pictures()
        if hand:
            show_picture(frame, chip, at=hand.pinch_center)

        state = "ON" if pictures_visible() else "OFF"
        show_text(frame, f"Pictures: {state}", at=(20, 40))
        show_text(frame, "Double pinch to toggle. Q to quit.", at=(20, 75), scale=0.6)
        if not camera.show(frame):
            break
