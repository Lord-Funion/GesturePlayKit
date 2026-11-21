# Changelog

## 1.2.0 — Easy overlay visibility

- Add `hide_all_pictures()`, `show_all_pictures()`, `toggle_pictures()`, `pictures_visible()`, and `set_pictures_visible()`.
- All `show_picture()` calls now respect the global visibility flag; hidden overlays don't fetch remote images.
- Add an example and tests for toggling overlays while keeping webcam and text visible.
- No breaking changes to the tracking or rendering API.

## 1.1.0 — Expanded tracking and documentation
- Face: 478 landmark positions, mouth shape, smile and wink approximations, eye closures, two-eye blink transitions, 52 optional MediaPipe blendshape coefficients, optional transformation matrix.
- Hands: estimated handedness, indexed normalized/world coordinates, finger count, pointing and peace sign, palm width and pinch strength, and bounding box.
- Optional full-body pose tracking using MediaPipe Pose Landmarker Lite: 33 landmarks, named joints, angles, arm-raised heuristic, skeleton renderer, visibility.
- `download_models(poses=True)` and CLI `download-models --poses` / `--poses-only`.
- Better beginner tutorials, complete API reference, landmark tables, recipes and troubleshooting.
- Preserved the version 1.0 public imports and default hand + face behavior.

## 1.0.0 — First stable API
- Hand and face tracking, pinches and double-pinches, overlays, helper functions, model download CLI and sample programs.
