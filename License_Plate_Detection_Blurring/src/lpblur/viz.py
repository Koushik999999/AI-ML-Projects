"""Visualisation helpers: ground-truth overlays and before/after grids."""

from __future__ import annotations

import os
from typing import Any, Sequence

import cv2
import numpy as np

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD
from lpblur.blur import anonymize, padded_box
from lpblur.coords import yolo_to_pixel


def draw_boxes(
    img_path: str, label_path: str, color: tuple[int, int, int] = (0, 255, 0), thickness: int = 2
) -> np.ndarray:
    """Overlay the ground-truth YOLO boxes on a raw image; returns an RGB array."""
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"cannot read image: {img_path}")
    h, w = img.shape[:2]
    if os.path.exists(label_path):
        with open(label_path) as fh:
            lines = fh.read().strip().splitlines()
        for line in lines:
            p = line.split()
            if len(p) < 5:
                continue
            cx, cy, bw, bh = map(float, p[1:5])
            x1, y1, x2, y2 = yolo_to_pixel(cx, cy, bw, bh, w, h)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def hide_plates(
    img: np.ndarray, boxes_xyxy: np.ndarray, pad: float = DEFAULT_PAD, color: tuple[int, int, int] = (0, 0, 0)
) -> np.ndarray:
    """Cover the same padded regions that `blur_plates` would blur with a solid colour (for publishable figures)."""
    out = img.copy()
    h_img, w_img = img.shape[:2]
    for b in boxes_xyxy:
        x1, y1, x2, y2 = padded_box(*b, w_img, h_img, pad)
        out[y1:y2, x1:x2] = color
    return out


def before_after(
    paths: Sequence[str],
    model: Any,
    title: str,
    conf: float = DEFAULT_CONF,
    pad: float = DEFAULT_PAD,
    imgsz: int = DEFAULT_IMGSZ,
    save_path: str | None = None,
    hide_original: bool = False,
):
    """Plot original vs blurred for each image path; optionally save the figure. Returns the figure.

    With hide_original=True the left panel has the plates covered by a black box, so no readable plate is shown.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(len(paths), 2, figsize=(10, 3.6 * len(paths)), squeeze=False)
    for i, p in enumerate(paths):
        before, after, boxes = anonymize(p, model, conf, pad, imgsz)
        if hide_original:
            before = hide_plates(before, boxes, pad)
        ax[i, 0].imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))
        ax[i, 0].set_title("original (plate hidden for this README)" if hide_original else "original")
        ax[i, 1].imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))
        ax[i, 1].set_title(f"blurred ({len(boxes)} plate(s) found)")
        for a in ax[i]:
            a.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=100)
    return fig
