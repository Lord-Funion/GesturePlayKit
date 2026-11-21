# Landmark reference

All `.landmark(n)` calls return `(x, y)` **in pixels on the current frame**. Indexing follows Google's MediaPipe definitions. Internally, `normalized_points` hold `(x, y, z)` where `x` and `y` are normalized; some trackers also expose `world_points` estimates.

## Hand: 21 landmarks per detected hand

| Number | Point |
|---:|---|
| 0 | Wrist |
| 1 | Thumb CMC |
| 2 | Thumb MCP |
| 3 | Thumb IP |
| 4 | Thumb tip |
| 5 | Index MCP |
| 6 | Index PIP |
| 7 | Index DIP |
| 8 | Index tip |
| 9 | Middle MCP |
| 10 | Middle PIP |
| 11 | Middle DIP |
| 12 | Middle tip |
| 13 | Ring MCP |
| 14 | Ring PIP |
| 15 | Ring DIP |
| 16 | Ring tip |
| 17 | Pinky MCP |
| 18 | Pinky PIP |
| 19 | Pinky DIP |
| 20 | Pinky tip |

Example `hand.touching(4, 8)` estimates contact between thumb and index tips. `hand.palm_center` averages points 0, 5, 9, 13 and 17; this is a heuristic, not a dedicated model output.

## Face: 478 landmarks

| Number | Point / rough region |
|---:|---|
| 1 | Nose tip |
| 10 | Forehead |
| 13 | Upper inner lip |
| 14 | Lower inner lip |
| 61 and 291 | Mouth corners |
| 33 and 133 | First eye horizontal bounds |
| 159 and 145 | First eye upper/lower lids |
| 362 and 263 | Second eye horizontal bounds |
| 386 and 374 | Second eye upper/lower lids |
| 152 | Chin |
| 468–472 | Iris landmarks for one eye (when emitted) |
| 473–477 | Iris landmarks for the other eye (when emitted) |

Facial blendshapes are **separate from landmarks**. Examples: `eyeBlinkLeft`, `eyeBlinkRight`, `jawOpen`, `mouthSmileLeft`, `mouthSmileRight`, `browDownLeft`, `browInnerUp`, `mouthFunnel`. See Google's [Face Landmarker guide](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker) for all 52 coefficients and the full mesh topology.

## Body: 33 landmarks

Use readable names with `pose.landmark("left_wrist")`, or numeric indices. Name-to-index mapping:

```
0 nose               1 left_eye_inner     2 left_eye
3 left_eye_outer     4 right_eye_inner    5 right_eye
6 right_eye_outer    7 left_ear           8 right_ear
9 mouth_left        10 mouth_right       11 left_shoulder
12 right_shoulder   13 left_elbow        14 right_elbow
15 left_wrist       16 right_wrist       17 left_pinky
18 right_pinky      19 left_index        20 right_index
21 left_thumb       22 right_thumb       23 left_hip
24 right_hip        25 left_knee         26 right_knee
27 left_ankle       28 right_ankle       29 left_heel
30 right_heel       31 left_foot_index   32 right_foot_index
```

`pose.visibility(...)` is the model's estimated visibility (0..1). If a joint is hidden, any angle involving it may be inaccurate. Refer to [Pose Landmarker docs](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker).
