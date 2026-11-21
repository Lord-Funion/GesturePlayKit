"""Pose demo. First run: python -m gestureplaykit download-models --poses-only"""
from gestureplaykit import Camera, Vision, draw_pose, show_text

with Camera() as camera, Vision(hands=False, faces=False, poses=True) as vision:
    while (frame := camera.read()) is not None:
        vision.update(frame)
        if vision.pose:
            draw_pose(frame, vision.pose)
            show_text(frame, f"Elbow: {vision.pose.left_elbow_angle:.0f} degrees", at=(15, 35))
            if vision.pose.arms_raised:
                show_text(frame, "ARMS RAISED!", at=(15, 70))
        if not camera.show(frame):
            break
