"""Track both hands and draw landmark skeletons and a rectangle on screen."""
from gestureplaykit import Camera, Vision, draw_hand, show_text, show_rectangle, inside_rectangle

with Camera() as camera, Vision(models_dir="models", faces=False) as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        target = (230, 140, 400, 290)
        show_rectangle(frame, target, color=(255, 120, 0))
        for hand in vision.hands:
            draw_hand(frame, hand, number_landmarks=False)
            if inside_rectangle(hand.palm_center, target):
                show_text(frame, f"HAND {hand.id} IN BOX", at=(15, 65))
            if hand.open_palm:
                show_text(frame, "OPEN PALM!", at=(15, 100))
        if not camera.show(frame, title="Hand and shape demo"):
            break
