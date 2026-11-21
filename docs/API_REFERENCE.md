# GesturePlayKit 1.2.0 — Complete API reference

**This is the complete documented public surface for v1.2.0.** Examples use OpenCV BGR pixel coordinates `(x, y)` and BGR colors `(blue, green, red)` unless noted.

## Install / models / version

```bash
python -m pip install .
python -m gestureplaykit --version
python -m gestureplaykit download-models
python -m gestureplaykit download-models --poses
python -m gestureplaykit download-models --hands-only
python -m gestureplaykit download-models --faces-only
python -m gestureplaykit download-models --poses-only
```

### `download_models(folder="models", *, overwrite=False, hands=True, faces=True, poses=False)`

Downloads official MediaPipe models to a directory for **subsequent offline use**. Returns a tuple of `Path` values. Only pass `poses=True` if you want the optional Pose Landmarker Lite. Existing files remain untouched unless `overwrite=True`.

### `model_paths(folder="models")`

Returns `(hand_model_path, face_model_path)` for compatibility with v1.0.0.

### `pose_model_path(folder="models")`

Returns the path of the optional `pose_landmarker_lite.task` file.

### `gestureplaykit.__version__`

The package version string, currently `1.2.0`.

## Camera class

### `Camera(index=0, width=640, height=480, mirror=True)`

Create a webcam wrapper. Use it as a context manager to ensure the camera is released. See `camera.py` for exact settings and back-end behavior.

- `camera.read()` — returns the latest OpenCV BGR NumPy frame or `None` if no frame is available.
- `camera.show(frame, title="GesturePlayKit")` — shows the image and returns `False` if the user presses **Q** or **Escape**; returns `True` otherwise.
- `camera.close()` — releases the camera and closes the program's display window.
- `with Camera() as camera:` — recommended lifetime pattern.

## Vision class

### `Vision(models_dir="models", hands=True, faces=True, max_hands=2, pinch_start=0.35, pinch_release=0.50, double_pinch_window=0.60, mouth_open_ratio=0.20, mouth_closed_ratio=0.12, poses=False, max_poses=1, face_blendshapes=True, face_transformations=False)`

Use inside `with Vision(...) as vision:`. By default tracks hands and face; full body is **off** until `poses=True`. Specify `hands=False`, `faces=False`, or `poses=False` to avoid unnecessary CPU work. Models must be downloaded separately.

- `vision.update(frame)` — process exactly one BGR `uint8` image; returns `vision` for method chaining. Call once per frame.
- `vision.hands` — list of `Hand` objects (empty if none).
- `vision.hand` — first detected `Hand` or `None`.
- `vision.face` — first detected `Face` or `None`.
- `vision.poses` — list of detected `Pose` objects (empty if none).
- `vision.pose` — first detected `Pose` or `None`.
- `vision.reset()` — clear hand identity and gesture histories; useful when switching scenes.
- `vision.close()` — release trackers; safe to call more than once.

**Important:** event flags are valid for the **current frame only**. `vision.hand` and `vision.face` may become `None` when the person leaves the frame. All tracking is an estimate, not proof of touch, mouth contact, identity, or intent.

## Hand class — 21 points per hand

`hand = vision.hand` (check for `None` before accessing).

| Attribute/method | Meaning / return |
|---|---|
| `hand.id` | Temporary best-effort integer tracking ID (not biometric identity) |
| `hand.handedness` | MediaPipe label such as `Left` or `Right`, or `None` |
| `hand.handedness_score` | MediaPipe label confidence or `None` |
| `hand.points` | Tuple of 21 `(x,y)` integer pixel points |
| `hand.normalized_points` | Tuple of 21 `(x,y,z)` normalized coordinates, if supplied |
| `hand.world_points` | Tuple of model-estimated 3D `(x,y,z)` coordinates, if supplied |
| `hand.landmark(8)` | Pixel position of landmark 8 (index fingertip); valid 0..20 |
| `hand.wrist` | Landmark 0 in pixels |
| `hand.thumb_tip` | Landmark 4 in pixels |
| `hand.index_tip` | Landmark 8 in pixels |
| `hand.palm_center` | Approximate center of palm in pixels |
| `hand.pinch_center` | Midpoint between thumb tip and index tip |
| `hand.distance(4,8)` | Pixel distance between arbitrary hand landmarks |
| `hand.touching(4,8,ratio=0.35)` | Estimate whether two points are close vs palm width |
| `hand.palm_width` | Distance between landmarks 5 and 17 |
| `hand.pinch_strength` | Approximate 0..1 strength derived from fingertip separation |
| `hand.pinching` | Held pinch state |
| `hand.pinch_started` | One-frame event: new pinch begins |
| `hand.pinch_ended` | One-frame event: release while hand remains tracked |
| `hand.double_pinched` | One-frame event: second pinch began within configured window |
| `hand.finger_up("index")` | Estimate whether a named finger is extended |
| `hand.fingers_up` | Dictionary of thumb/index/middle/ring/pinky booleans |
| `hand.raised_finger_count` | Number of extended fingers (0..5) |
| `hand.open_palm` | Approximate extended non-thumb fingers |
| `hand.fist` | Approximate folded non-thumb fingers |
| `hand.peace_sign` | Approximate index+middle raised only |
| `hand.pointing` | Approximate index raised without other non-thumb fingers |
| `hand.bounding_box` | `(left,top,right,bottom)` enclosing landmark coordinates |

Finger names: `thumb`, `index`, `middle`, `ring`, `pinky`. All shape and contact heuristics can fail if a hand is sideways or obscured.

## Face class — 478 points, expression scores

`face = vision.face`. When `face_blendshapes=True` (default), the model may report facial expression coefficients. Scores are numeric **model outputs**, not emotional or psychological measurements.

| Attribute/method | Meaning / return |
|---|---|
| `face.points` | 478 `(x,y)` pixel coordinates |
| `face.normalized_points` | 478 `(x,y,z)` model coordinates if available |
| `face.landmark(13)` | Pixel location of a landmark; validates index |
| `face.distance(13,14)` | Pixel distance between two facial landmarks |
| `face.bounding_box` | Box enclosing face landmarks |
| `face.face_center` | Center of face bounding box |
| `face.nose_tip` | Landmark 1 |
| `face.forehead` | Landmark 10 |
| `face.chin` | Landmark 152 |
| `face.mouth_center` | Midpoint between inner lips (13 and 14) |
| `face.mouth_width` | Mouth corner distance (61 to 291) in pixels |
| `face.mouth_height` | Inner lip distance (13 to 14) in pixels |
| `face.mouth_ratio` | Mouth height divided by mouth width |
| `face.mouth_open` | Held mouth-open state with hysteresis |
| `face.mouth_closed` | Inverse of mouth_open |
| `face.mouth_just_opened` | One-frame event: mouth changes to open |
| `face.mouth_just_closed` | One-frame event: mouth changes to closed |
| `face.near_mouth((x,y), max_distance=70)` | Is a pixel point within a radius of mouth center? |
| `face.left_eye_center`, `face.right_eye_center` | Approximate eye centers |
| `face.eye_open_ratio("left")` | 2D eyelid gap / eye width (approximate) |
| `face.eye_open_ratio("right")` | Right counterpart |
| `face.blendshapes` | Dictionary of named expression values, or empty when not enabled |
| `face.expression("jawOpen", default=0.0)` | Get one named blendshape score |
| `face.smiling` | Heuristic based on left/right mouthSmile blendshapes |
| `face.left_eye_closed`, `face.right_eye_closed` | Heuristic based on eyeBlink blendshapes |
| `face.eyes_closed` | Both model eyelid scores above threshold |
| `face.winking` | One eyelid score above threshold, other below |
| `face.blink_started`, `face.blink_ended` | One-frame transition events when both eyes close/reopen |
| `face.transformation_matrix` | Optional facial 4×4 transform matrix, or `None` |

Popular blendshapes include `eyeBlinkLeft`, `eyeBlinkRight`, `jawOpen`, `mouthSmileLeft`, `mouthSmileRight`, `browInnerUp`, `mouthPucker`, `mouthFunnel`, `cheekPuff` and others. See MediaPipe's official list for all 52.

## Pose class — 33 body points (opt in)

`pose = vision.pose` after initializing `Vision(poses=True)` and downloading the optional model.

| Attribute/method | Meaning / return |
|---|---|
| `pose.points` | Tuple of 33 `(x,y)` pixel coordinates |
| `pose.normalized_points` | Model `(x,y,z)` coordinates |
| `pose.world_points` | Model-estimated 3D points (when available) |
| `pose.visibilities` | Model-estimated per-joint visibility confidence |
| `pose.landmark(15)` | Body landmark by integer 0..32 |
| `pose.landmark("left_wrist")` | Same point using one of the 33 joint names |
| `pose.visibility("left_wrist")` | Estimated visible fraction/confidence 0..1 |
| `pose.distance("left_wrist", "right_wrist")` | Pixel distance |
| `pose.angle(a, center, c)` | Angle at center, in degrees (0..180) |
| `pose.left_elbow_angle`, `pose.right_elbow_angle` | Joint angles derived from 2D projections |
| `pose.left_knee_angle`, `pose.right_knee_angle` | Knee angles from 2D projections |
| `pose.shoulders_center`, `pose.hips_center` | Midpoint between left/right body joints |
| `pose.arms_raised` | Both wrists appear above their shoulders |
| `pose.bounding_box` | Bounding box enclosing 33 tracked body points |
| `draw_pose(frame, pose, color=(90,245,90), radius=4, number_landmarks=False, minimum_visibility=0.4)` | Draw skeleton onto frame |

**Angles are 2D projections** and can differ dramatically from 3D anatomical joint angles. Use `visibility()` to reject occluded joints and do not treat this as a clinical measuring tool.

## Pictures, rendering, and colors

| Function | What it does |
|---|---|
| `load_picture(source, size=None)` | Read image from local path or direct HTTP(S) PNG/JPG URL. PNG alpha retained. |
| `resize_picture(picture, size)` | Resize existing BGR/BGRA image. `size=(width,height)` |
| `hide_all_pictures()` | Disable subsequent picture overlays across this Python process |
| `show_all_pictures()` | Re-enable picture overlays |
| `toggle_pictures()` | Flip picture visibility; return new Boolean visibility |
| `pictures_visible()` | Return whether picture overlays are currently visible (default `True`) |
| `set_pictures_visible(True or False)` | Explicitly set picture visibility; `TypeError` for non-Boolean values |
| `show_picture(frame, picture, at=(x,y), size=None, opacity=1.0)` | Centered image overlay, clipping at edges, alpha-aware, opacity 0..1 |
| `show_text(frame, text, at=(15,35), color=(255,255,255), scale=0.7, thickness=2)` | Draw text at pixel location |
| `show_point(frame, at, color=(0,255,255), radius=7)` | Filled circular dot |
| `show_line(frame, start, end, color=(255,255,255), thickness=2)` | Draw connecting line |
| `show_rectangle(frame, rect, color=(255,255,255), thickness=2, fill=False)` | Draw box from `(left,top,right,bottom)` |
| `draw_hand(frame, hand, color=(0,255,255), number_landmarks=False, radius=4)` | Draw hand skeleton and optional numbers |
| `draw_pose(...)` | Draw body pose skeleton (see above) |

All rendering functions **modify `frame` in place** and return it for chaining. Picture visibility affects `show_picture` only: text, lines, and landmark drawing are unchanged. The setting is process-wide; toggling it cannot erase picture pixels already drawn into an existing frame, but newly captured frames have no previous overlays. Hidden `show_picture` calls skip loading path/URL images. `load_picture()` caches decoded images and returns a copy. Avoid downloading inside the frame loop. Remote image URL requests require internet, even if the tracking models were downloaded for offline operation.

## Geometry helpers

| Function | Meaning |
|---|---|
| `distance((x1,y1), (x2,y2))` | Euclidean pixel distance |
| `clamp(value, min_value, max_value)` | Limit a numeric value to a range |
| `inside_rectangle((x,y), (left,top,right,bottom))` | Check if point falls inside rectangle |

## Migrating from v1.0.0

All public v1.0.0 names remain importable. Default `Vision()` still tracks hands and face, not body. New kwargs are optional, and pose models are downloaded separately. `Face` and `Hand` include additional optional fields with defaults for compatibility. If you rely on `handedness`, note mirrored-camera orientation. This package does **not** perform face recognition/identity verification.

## Support / limitations

- Face blendshape scores and hand gestures are **approximations** and may be wrong due to occlusion, backlighting, side views, or low resolution.
- Hand IDs are temporary estimates; body tracking provides no long-term identity matching.
- Frame processing may become slow if hands, face, and pose detectors all run together on weak CPUs.
- Python version support also depends on available MediaPipe wheels (not guaranteed for every interpreter).
- Google models are separate downloads and have their own licensing terms.
- For the library's development history and attribution, see [AI_ATTRIBUTION.md](../AI_ATTRIBUTION.md).
