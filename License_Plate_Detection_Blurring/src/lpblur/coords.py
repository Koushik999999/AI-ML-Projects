"""YOLO <-> pixel coordinate conversion and label reading."""

from __future__ import annotations

import os

import numpy as np


def yolo_to_pixel(
    cx: float, cy: float, w: float, h: float, img_w: int, img_h: int
) -> tuple[int, int, int, int]:
    """Normalised YOLO (cx, cy, w, h) -> integer pixel corners (x1, y1, x2, y2), clamped to the image."""
    x1 = int(round((cx - w / 2) * img_w))
    y1 = int(round((cy - h / 2) * img_h))
    x2 = int(round((cx + w / 2) * img_w))
    y2 = int(round((cy + h / 2) * img_h))
    return max(0, x1), max(0, y1), min(img_w - 1, x2), min(img_h - 1, y2)


def pixel_to_yolo(
    x1: float, y1: float, x2: float, y2: float, img_w: int, img_h: int
) -> tuple[float, float, float, float]:
    """Inverse transform: pixel corners -> normalised YOLO (cx, cy, w, h)."""
    return (x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h, (x2 - x1) / img_w, (y2 - y1) / img_h


def read_gt(label_path: str, img_w: int, img_h: int) -> np.ndarray:
    """Ground-truth boxes of one image as float pixel corners (not clamped), shape (n, 4)."""
    out = []
    if os.path.exists(label_path):
        with open(label_path) as fh:
            lines = fh.read().strip().splitlines()
        for line in lines:
            p = line.split()
            if len(p) >= 5:
                cx, cy, w, h = map(float, p[1:5])
                out.append(
                    [(cx - w / 2) * img_w, (cy - h / 2) * img_h, (cx + w / 2) * img_w, (cy + h / 2) * img_h]
                )
    return np.array(out).reshape(-1, 4)
