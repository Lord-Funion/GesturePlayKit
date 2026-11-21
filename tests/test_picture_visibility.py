"""Picture visibility: hide/show/toggle without affecting other overlays."""

import numpy as np
import pytest

from gestureplaykit import (
    show_picture, show_text, hide_all_pictures, show_all_pictures,
    set_pictures_visible, pictures_visible, toggle_pictures,
)


@pytest.fixture(autouse=True)
def restore_visibility():
    show_all_pictures()
    yield
    show_all_pictures()


def test_defaults_on_and_toggles():
    assert pictures_visible() is True
    hide_all_pictures()
    assert pictures_visible() is False
    assert toggle_pictures() is True
    assert toggle_pictures() is False
    show_all_pictures()
    assert pictures_visible() is True


def test_hide_skips_all_picture_draws_and_keeps_text():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    image = np.full((10, 10, 3), 255, dtype=np.uint8)
    hide_all_pictures()
    assert show_picture(frame, image, at=(50, 50)) is frame
    assert not frame.any()
    show_text(frame, "still visible", at=(2, 50), scale=0.5)
    assert frame.any()


def test_show_after_hiding_and_existing_pixels():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    image = np.full((5, 5, 3), 199, dtype=np.uint8)
    show_picture(frame, image, at=(10, 10))
    hide_all_pictures()
    assert frame[10, 10, 0] == 199  # in-place drawing cannot be reversed
    next_frame = np.zeros((20, 20, 3), dtype=np.uint8)
    show_picture(next_frame, image, at=(10, 10))
    assert not next_frame.any()
    show_all_pictures()
    show_picture(next_frame, image, at=(10, 10))
    assert next_frame[10, 10, 0] == 199


def test_hidden_path_not_opened(tmp_path):
    hide_all_pictures()
    frame = np.zeros((30, 30, 3), dtype=np.uint8)
    show_picture(frame, tmp_path / "missing-file.png", at=(10, 10))
    assert not frame.any()
    show_all_pictures()
    with pytest.raises(FileNotFoundError):
        show_picture(frame, tmp_path / "missing-file.png", at=(10, 10))


def test_explicit_visibility_validation():
    set_pictures_visible(False)
    assert not pictures_visible()
    set_pictures_visible(True)
    assert pictures_visible()
    with pytest.raises(TypeError):
        set_pictures_visible("False")
    with pytest.raises(TypeError):
        set_pictures_visible(0)
