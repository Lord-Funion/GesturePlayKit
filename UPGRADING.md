# Upgrading from GesturePlayKit 1.0.0

All existing v1.0 public names and the original default `Vision()` behavior remain. If you want body tracking, run `python -m gestureplaykit download-models --poses` and pass `Vision(poses=True)`.

New: `vision.pose`, `vision.poses`, `Pose`, `draw_pose`; extra Hand fields (`handedness`, `pinch_strength`, `raised_finger_count`, `peace_sign`, etc.); extra Face fields (`smiling`, `winking`, `eyes_closed`, `blink_started`, `expression('jawOpen')`, etc.).

Existing apps may see additional CPU usage from the now enabled-by-default Face Landmarker blendshapes. If not needed, set `Vision(face_blendshapes=False)`.

Important: models remain separate downloads and Python package availability depends on the platform and interpreter.
