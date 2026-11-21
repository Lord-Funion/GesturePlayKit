"""Use all trackers at once (requires three downloaded models)."""
from gestureplaykit import Camera, Vision, draw_hand, draw_pose, show_text

with Camera() as camera, Vision(poses=True) as vision:
    while (frame := camera.read()) is not None:
        vision.update(frame)
        for hand in vision.hands:
            draw_hand(frame, hand)
        if vision.face and vision.face.mouth_open:
            show_text(frame, "MOUTH OPEN", at=(15, 35))
        if vision.pose:
            draw_pose(frame, vision.pose)
        if not camera.show(frame):
            break
