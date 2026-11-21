# Upgrading to GesturePlayKit 1.3.0

Version 1.3.0 adds optional sound effects; all v1.2.0 tracking, picture, camera,
and geometry functions remain compatible. Use `play_effect("pop")` for a short
built-in effect or `play_sound("mysound.wav")` for a custom file. WAV effects
work on Windows with no extra dependency. For non-Windows systems, sound volume
control or overlapping effects, install the optional `audio` extra with Pygame:
`python -m pip install "gestureplaykit[audio]"` after publication, or
`python -m pip install ".[audio]"` from source.

## Changes introduced in 1.2.0

Version 1.2.0 adds `hide_all_pictures()`, `show_all_pictures()`, `toggle_pictures()`, `pictures_visible()` and `set_pictures_visible(bool)`. These only affect future `show_picture()` calls, not text or webcam video. The default is visible, so existing code keeps working. The setting is process-wide.

## Changes introduced in v1.1.0

All existing v1.0 public names and the original default `Vision()` behavior remain. If you want body tracking, run `python -m gestureplaykit download-models --poses` and pass `Vision(poses=True)`.

New: `vision.pose`, `vision.poses`, `Pose`, `draw_pose`; extra Hand fields (`handedness`, `pinch_strength`, `raised_finger_count`, `peace_sign`, etc.); extra Face fields (`smiling`, `winking`, `eyes_closed`, `blink_started`, `expression('jawOpen')`, etc.).

Existing apps may see additional CPU usage from the now enabled-by-default Face Landmarker blendshapes. If not needed, set `Vision(face_blendshapes=False)`.

Important: models remain separate downloads and Python package availability depends on the platform and interpreter.
