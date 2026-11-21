"""Official Google MediaPipe task-model downloading (not bundled in wheel)."""
from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

MODELS = {
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "pose_landmarker_lite.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
}
MAX_MODEL_BYTES = 50 * 1024 * 1024


def model_paths(folder="models") -> tuple[Path, Path]:
    """Paths of expected hand and face models within ``folder``."""
    folder = Path(folder).expanduser()
    return folder / "hand_landmarker.task", folder / "face_landmarker.task"


def pose_model_path(folder="models") -> Path:
    """Path to the optional Pose Landmarker Lite task file."""
    return Path(folder).expanduser() / "pose_landmarker_lite.task"


def download_models(folder="models", *, overwrite=False,
                    hands=True, faces=True, poses=False) -> tuple[Path, ...]:
    """Download selected Google MediaPipe models once for later offline use.

    By default downloads both. ``hands=True, faces=False`` downloads only the
    hand model. Existing files aren't overwritten unless ``overwrite=True``.
    Returns downloaded/existing paths in hand-then-face order.
    """
    if not hands and not faces and not poses:
        raise ValueError("Enable hands, faces and/or poses")
    folder = Path(folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    names = ((["hand_landmarker.task"] if hands else [])
             + (["face_landmarker.task"] if faces else [])
             + (["pose_landmarker_lite.task"] if poses else []))
    paths = []
    for name in names:
        path = folder / name
        if overwrite or not path.is_file():
            temporary = folder / (name + ".part")
            try:
                with urlopen(Request(MODELS[name], headers={"User-Agent": "GesturePlayKit/1.1"}), timeout=30) as response:
                    count = 0
                    with temporary.open("wb") as output:
                        while True:
                            block = response.read(1024 * 1024)
                            if not block:
                                break
                            count += len(block)
                            if count > MAX_MODEL_BYTES:
                                raise ValueError(f"Downloaded model exceeds {MAX_MODEL_BYTES // (1024*1024)} MB")
                            output.write(block)
                if count < 1024:
                    raise ValueError(f"Downloaded model seems incomplete: {name}")
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        paths.append(path)
    return tuple(paths)
