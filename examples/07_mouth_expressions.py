"""Display mouth-open, blinking, smile and expression values. Press Q or Escape."""
from gestureplaykit import Camera, Vision, show_text

with Camera() as camera, Vision(hands=False, faces=True) as vision:
    while (frame := camera.read()) is not None:
        vision.update(frame)
        face = vision.face
        if face:
            show_text(frame, "Mouth open: " + str(face.mouth_open), at=(15, 35))
            show_text(frame, "Mouth ratio: " + f"{face.mouth_ratio:.2f}", at=(15, 65))
            show_text(frame, "Jaw open score: " + f"{face.expression('jawOpen'):.2f}", at=(15, 95))
            show_text(frame, "Smiling: " + str(face.smiling), at=(15, 125))
            show_text(frame, "Winking: " + str(face.winking), at=(15, 155))
            if face.blink_started:
                print("Blink started")
        if not camera.show(frame):
            break
