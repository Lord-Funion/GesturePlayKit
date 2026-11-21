# Recipes: build something useful

All snippets below belong **inside** the frame loop after calling `vision.update(frame)`, unless noted.

## Put a chip between two fingers

```python
if vision.hand and vision.hand.pinching:
    show_picture(frame, chip, at=vision.hand.pinch_center)
```

Load the chip **once outside the loop**: `chip = load_picture("chip.png", size=(100, 100))`.

## Make a single-action counter

```python
if vision.hand and vision.hand.pinch_started:
    pinch_count += 1
```

Initialize `pinch_count = 0` before the loop. Avoid `if hand.pinching: pinch_count += 1` unless counting every frame is intended.

## Pinch to spawn, then double-pinch to freeze

```python
if vision.hand:
    if vision.hand.pinching and not frozen:
        position = vision.hand.pinch_center
    if vision.hand.double_pinched:
        frozen = not frozen
if frozen:
    show_picture(frame, chip, at=position)
```

Initialize `frozen = False` and `position = (320, 240)` before the loop. This is an illustrative starting point; real apps should manage lost-hand states and object lifetimes.

## Open mouth + chip near mouth

```python
face = vision.face
if face and face.mouth_open and face.near_mouth(chip_position, 80):
    show_text(frame, "CHOMP READY", at=(20, 100))
if face and face.mouth_just_closed:
    print("Mouth closed!")
```

To count an actual virtual bite, combine the 'open near chip' state with a later 'close near chip' event, and clear that state after counting. The detector **cannot know if any object was physically eaten**.

## Use facial expressions

```python
face = vision.face
if face:
    if face.smiling:
        show_text(frame, "SMILE!", at=(20, 60))
    if face.blink_started:
        print("Both eyes closed")
    if face.winking:
        print("Only one eye is closed")
    show_text(frame, f"Jaw: {face.expression('jawOpen'):.2f}", at=(20, 100))
```

All expression scores are estimated probabilities/intensities, not mind reading.

## Measure elbows or knees

```python
pose = vision.pose
if pose:
    draw_pose(frame, pose)
    show_text(frame, f"Elbow: {pose.left_elbow_angle:.0f} deg", at=(20, 70))
    if pose.arms_raised:
        show_text(frame, "ARMS UP", at=(20, 120))
```

You must initialize `Vision(poses=True)` and download the optional pose model first.

## Multiple hands

```python
for hand in vision.hands:
    draw_hand(frame, hand)
    if hand.pinch_started:
        print("Hand event", hand.id, hand.handedness)
```

Hand IDs are temporary, not biometric identifiers.

## Screenshots and recordings

GesturePlayKit returns regular OpenCV frames, so you can save a snapshot with `cv2.imwrite("screenshot.png", frame)` or build a video writer yourself. Respect webcam privacy when recording other people.

## Hide or show every picture overlay

```python
from gestureplaykit import hide_all_pictures, show_all_pictures, toggle_pictures

hide_all_pictures()  # disable overlays from show_picture()
show_all_pictures()  # enable them again
# or call toggle_pictures() from a key press or gesture event
```

Only picture overlays are hidden. Text, geometry and landmarks still draw; webcam frames are unaffected. In each camera-loop iteration, read a new frame before drawing overlays. See `examples/10_toggle_pictures.py`.
