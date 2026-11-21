"""Tiny, dependency-free geometry helpers for webcam apps."""
from __future__ import annotations
import math
from typing import Sequence


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Euclidean distance between 2-D coordinates."""
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside inclusive bounds."""
    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")
    return max(minimum, min(float(value), maximum))


def inside_rectangle(point: Sequence[float], rect: Sequence[float]) -> bool:
    """Test if (x,y) lies in (left,top,right,bottom), including edges."""
    x, y = point
    left, top, right, bottom = rect
    if left > right or top > bottom:
        raise ValueError("rectangle bounds must be ordered")
    return left <= x <= right and top <= y <= bottom
