# Getting started

## 1. Install

Open PowerShell in the repository directory:

```powershell
py -m pip install --upgrade .
py -m gestureplaykit download-models --poses
py -m gestureplaykit --version
```

Expected version: `GesturePlayKit 1.1.0`. If your OS cannot install a compatible MediaPipe wheel, try a supported Python version in an isolated virtual environment. Do not downgrade packages blindly.

You may omit `--poses` if you only use hands and face. The downloaded `models/` directory is relative to your working directory. For scripts run from another directory, supply `Vision(models_dir=r"C:\myproject\models")`.

## 2. Understand the frame loop

`Camera.read()` returns one BGR NumPy image. `Vision.update(frame)` runs detectors and updates properties (`vision.hand`, `vision.face`, `vision.pose`). Make the changes you want by calling drawing functions, and finally call `camera.show(frame)`. Only put image downloads and asset loading **outside** the main loop.

```python
from gestureplaykit import Camera, Vision, show_picture, load_picture

chip = load_picture("chip.png", size=(96, 96))
with Camera() as camera, Vision() as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        if vision.hand and vision.hand.pinching:
            show_picture(frame, chip, at=vision.hand.pinch_center)
        if not camera.show(frame):
            break
```

## 3. Gesture events vs states

`hand.pinching` is `True` for **every frame** while pinched. `hand.pinch_started` is `True` on **one frame** at the moment the pinch begins. `hand.double_pinched` occurs when the second pinch begins within the timing window (after a release). `face.mouth_just_closed` is a one-frame event; `face.mouth_open` is a held state. For counters, use one-frame events to avoid counting dozens of times.

## 4. Optional models / offline use

```powershell
py -m gestureplaykit download-models --hands-only
py -m gestureplaykit download-models --faces-only
py -m gestureplaykit download-models --poses-only
```

After downloading models once, these detectors run locally and do not upload frames. `load_picture("https://...")` still accesses the internet when fetching an image; for offline demos save it locally.

## 5. Select tracking features for speed

- `Vision(hands=True, faces=False)` — hands only
- `Vision(hands=False, faces=True)` — face only, including expression scores
- `Vision(hands=False, faces=False, poses=True)` — body only
- `Vision(poses=True)` — hands + face + body (more CPU load)

Use `Vision(max_hands=2, max_poses=1, face_blendshapes=True, face_transformations=False)` to tune tracking. A mirrored webcam can confuse left/right labels; check visually.
