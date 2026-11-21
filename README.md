# GesturePlayKit 1.1.0 🖐️👄🕺

**Make webcam games, interactive art, virtual props, motion controls, and experimental AR using simple Python functions.**

GesturePlayKit wraps Google's MediaPipe Tasks: **21 hand landmarks**, **478 face landmarks**, **52 optional face-expression blendshapes**, and **33 optional body-pose landmarks**. You write your own rules, UI, achievements, art, and gameplay. Hand, mouth, eye, and body detections are approximations, **not guaranteed physical contact or medical measurements**.

> **Release:** Source code for v1.1.0. A GitHub push does not automatically upload to PyPI; see [publishing instructions](PUBLISH_TO_PYPI.md).

## Getting started

Python 3.10+ is supported when compatible MediaPipe binaries exist for your platform. Install from this repository:

```bash
python -m pip install .
python -m gestureplaykit download-models --poses
```

By default models go to `./models/`, relative to the directory from which you start your program. All detection operates **locally after the models are downloaded**. The `--poses` flag adds the optional body model; without it you only download hand and face models.

Try `examples/07_mouth_expressions.py` or this minimal script:

```python
from gestureplaykit import Camera, Vision, show_text

with Camera() as camera, Vision() as vision:
    while True:
        frame = camera.read()
        if frame is None:
            break
        vision.update(frame)
        if vision.hand and vision.hand.pinching:
            show_text(frame, "PINCH!", at=(20, 60))
        if vision.face and vision.face.mouth_open:
            show_text(frame, "MOUTH OPEN", at=(20, 100))
        if vision.face and vision.face.smiling:
            show_text(frame, "SMILING!", at=(20, 140))
        if not camera.show(frame):
            break
```

To use body tracking:

```python
from gestureplaykit import Camera, Vision, draw_pose
with Camera() as camera, Vision(hands=False, faces=False, poses=True) as vision:
    while (frame := camera.read()) is not None:
        vision.update(frame)
        if vision.pose:
            draw_pose(frame, vision.pose)
            if vision.pose.arms_raised:
                print("Hands up!")
        if not camera.show(frame):
            break
```

## Features

- Hand gestures: pinch hold/start/end/double, fingertip contact, open palm, fist, peace sign, pointing, finger count, palm position, estimated handedness, multiple-hand IDs, and approximate world coordinates.
- Face: mouth open/close events and position, eye positions, mouth width/height, blink events, smile, wink, brow/jaw and 52 other optional expression scores, 478 landmarks, and optional transformation matrix.
- Body: 33 pose landmarks, shoulders/hips centers, raised arms, elbow/knee angles, point visibility, and skeleton drawing.
- Image/overlay: local or HTTP(S) PNG/JPG, alpha blending, opacity, resizing, cropping to frame, text, points, lines and rectangles.
- Offline once models and any remote images have been downloaded; no camera data is uploaded by this library.
- Model downloader (`python -m gestureplaykit download-models`) and tested Python-first API.

## Complete documentation

- **[API Reference](docs/API_REFERENCE.md)** — every public class/property/function with examples
- **[Getting Started](docs/GETTING_STARTED.md)** — setup, models, and first webcam program
- **[Landmarks](docs/LANDMARKS.md)** — hand, mouth, eye, and pose numbering
- **[Recipes](docs/RECIPES.md)** — pinch effects, eye blinks, virtual eating, joint angles
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — installation, PATH, lighting, offline use
- **[Changelog](CHANGELOG.md)** and **[Development attribution](AI_ATTRIBUTION.md)**

## Important limitations

Camera and model accuracy depend on lighting, occlusion, frame rate, and angles. `hand.id` is best-effort and may change when hands leave or cross; detected handedness may appear reversed in a mirrored view. Pixel distances change with perspective. `Face.smiling`, blink detection, and `Pose.arms_raised` are heuristics and **not robust biometric or safety assessments**. Face tracking currently selects the first detected face. Models are downloaded separately; they are not included in the wheel.

## Credits and licenses

GesturePlayKit uses [MediaPipe](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker), OpenCV and NumPy. MediaPipe models have their own terms. See [LICENSE](LICENSE) (MIT) for the GesturePlayKit source and [Development attribution](AI_ATTRIBUTION.md) for its development history.
