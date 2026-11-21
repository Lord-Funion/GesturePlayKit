# Troubleshooting

**`FileNotFoundError: ...hand_landmarker.task`** — Run `python -m gestureplaykit download-models` in the directory where you run your script, or set `Vision(models_dir="path/to/models")`. For body tracking add `--poses`.

**`gestureplaykit.exe not on PATH`** — The package can still be run with `python -m gestureplaykit --version` and `python -m gestureplaykit download-models`.

**No webcam / black screen** — Check OS webcam permissions, close other camera applications, and try `Camera(index=1)` if the first camera is not correct.

**Slow FPS** — Try `Vision(hands=True, faces=False, poses=False)` or a lower camera resolution. Running all detectors simultaneously can be CPU-intensive.

**Mouth or pinch not registering** — Improve even lighting; remove obstructions; face the camera; use `hand.distance(4, 8)`, `hand.palm_width`, `face.mouth_ratio`, and `face.expression('jawOpen')` to calibrate thresholds. Avoid assuming all camera angles produce equal results.

**Hand labels reversed** — Mirrored webcam feeds may swap apparent left/right. The `hand.handedness` classification is the model's output, not a guarantee.

**`ValueError: frame must be...`** — `Vision.update()` expects an OpenCV BGR `uint8` frame with shape `(height, width, 3)`.

**`ModuleNotFoundError` after installation** — Use the **same Python interpreter** for `python -m pip install .` and `python script.py`. On Windows, `py -m pip ...` and `py script.py` are usually paired.

**Image URL fails** — `load_picture()` expects a direct accessible PNG/JPG file URL. Download a local PNG for offline demonstrations. Do not use a page URL as an image URL.

**PyPI** — Installing from your source folder does not publish the package. Build wheel/sdist and upload with Twine using your own account. API tokens should never appear in repository files or public issues.
