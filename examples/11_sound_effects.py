"""Demo original sound effects in GesturePlayKit; press Q to quit.

Sound on Windows works with built-in winsound. Other platforms can install
optional Pygame: python -m pip install '.[audio]'
"""
from gestureplaykit import Camera, Vision, play_effect, show_text, toggle_sounds, sounds_enabled

with Camera() as camera, Vision() as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)

        if vision.hand and vision.hand.pinch_started:
            play_effect("pop")
        if vision.face and vision.face.mouth_just_closed:
            play_effect("chomp")
        if vision.hand and vision.hand.double_pinched:
            toggle_sounds()

        state = "ON" if sounds_enabled() else "MUTED"
        show_text(frame, f"Sound: {state}", at=(20, 35))
        show_text(frame, "Pinch = pop; close mouth = chomp", at=(20, 65), scale=0.6)
        show_text(frame, "Double pinch = mute; Q = quit", at=(20, 90), scale=0.6)
        if not camera.show(frame):
            break
