# Changelog

## 1.1.0 — Expanded tracking and documentation
- Face: 478 landmark positions, mouth shape, smile and wink approximations, eye closures, two-eye blink transitions, 52 optional MediaPipe blendshape coefficients, optional transformation matrix.
- Hands: estimated handedness, indexed normalized/world coordinates, finger count, pointing and peace sign, palm width and pinch strength, and bounding box.
- Optional full-body pose tracking using MediaPipe Pose Landmarker Lite: 33 landmarks, named joints, angles, arm-raised heuristic, skeleton renderer, visibility.
- `download_models(poses=True)` and CLI `download-models --poses` / `--poses-only`.
- Better beginner tutorials, complete API reference, landmark tables, recipes and troubleshooting.
- Preserved the version 1.0 public imports and default hand + face behavior.

## 1.0.0 — First stable API
- Hand and face tracking, pinches and double-pinches, overlays, helper functions, model download CLI and sample programs.
