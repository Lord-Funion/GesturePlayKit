"""YOUR project: build your own game logic with the library's sensor events.

This intentionally doesn't implement a chip-eating game, currency, shop, save,
object freezing, or any other original application features. Add those yourself.
"""
from gestureplaykit import Camera, Vision, show_text


# YOUR WORK: Create and initialize your own score, shop and game state here.

with Camera() as camera, Vision(models_dir="models") as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)

        hand = vision.hand
        face = vision.face

        if hand and hand.pinch_started:
            # YOUR WORK: What happens when pinching begins?
            pass

        if hand and hand.double_pinched:
            # YOUR WORK: What happens when you pinch twice?
            pass

        if face and face.mouth_just_closed:
            # YOUR WORK: How would you decide whether a chip was eaten?
            pass

        # YOUR WORK: Draw your sprites, display your score, and implement rules.
        show_text(frame, "My game, powered by GesturePlayKit")
        if not camera.show(frame, title="My Original Project"):
            break
