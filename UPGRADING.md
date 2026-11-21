# Upgrading to GesturePlayKit 1.2.0

Version 1.2.0 adds `hide_all_pictures()`, `show_all_pictures()`, `toggle_pictures()`, `pictures_visible()` and `set_pictures_visible(bool)`. These only affect future `show_picture()` calls, not text or webcam video. The default is visible, so existing code keeps working. The setting is process-wide.

## Changes introduced in v1.1.0

All existing v1.0 public names and the original default `Vision()` behavior remain. If you want body tracking, run `python -m gestureplaykit download-models --poses` and pass `Vision(poses=True)`.

New: `vision.pose`, `vision.poses`, `Pose`, `draw_pose`; extra Hand fields (`handedness`, `pinch_strength`, `raised_finger_count`, `peace_sign`, etc.); extra Face fields (`smiling`, `winking`, `eyes_closed`, `blink_started`, `expression('jawOpen')`, etc.).

Existing apps may see additional CPU usage from the now enabled-by-default Face Landmarker blendshapes. If not needed, set `Vision(face_blendshapes=False)`.

Important: models remain separate downloads and Python package availability depends on the platform and interpreter.
