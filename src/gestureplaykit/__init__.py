"""GesturePlayKit: accessible building blocks for webcam and gesture apps.

The library provides tracking, rendering and geometry primitives; the
application decides what gestures mean and how its game rules work.
"""

from .camera import Camera
from .vision import Vision, Hand, Face
from .pose import Pose, draw_pose
from .pictures import (
    load_picture, resize_picture, show_picture, show_text, show_point,
    show_line, show_rectangle, draw_hand, hide_all_pictures, show_all_pictures,
    set_pictures_visible, pictures_visible, toggle_pictures,
)
from .geometry import distance, clamp, inside_rectangle
from .models import download_models, model_paths, pose_model_path
from .audio import (play_sound, play_effect, stop_sounds, mute_sounds, unmute_sounds,
                    toggle_sounds, sounds_enabled, set_sounds_enabled, available_effects)

__version__ = "1.3.0"

__all__ = [
    "Camera", "Vision", "Hand", "Face", "Pose", "draw_pose", "load_picture", "resize_picture",
    "show_picture", "show_text", "show_point", "show_line", "show_rectangle",
    "hide_all_pictures", "show_all_pictures", "set_pictures_visible",
    "pictures_visible", "toggle_pictures", "draw_hand", "distance", "clamp", "inside_rectangle", "download_models",
    "model_paths", "pose_model_path", "play_sound", "play_effect", "stop_sounds",
    "mute_sounds", "unmute_sounds", "toggle_sounds", "sounds_enabled",
    "set_sounds_enabled", "available_effects", "__version__",
]
