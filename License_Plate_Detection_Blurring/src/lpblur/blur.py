"""Detection and blurring: only the pixels inside each padded plate box are modified."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD


def load_model(weights: str) -> Any:
    """Load a YOLOv8 model from a weights file (imports ultralytics lazily)."""
    from ultralytics import YOLO

    return YOLO(weights)


def detect(model: Any, img: np.ndarray, conf: float = DEFAULT_CONF, imgsz: int = DEFAULT_IMGSZ) -> np.ndarray:
    """Run the detector on one BGR image; returns plate boxes as (n, 4) xyxy pixel coordinates."""
    return model.predict(img, conf=conf, imgsz=imgsz, verbose=False)[0].boxes.xyxy.cpu().numpy()


def padded_box(
    x1: float, y1: float, x2: float, y2: float, img_w: int, img_h: int, pad: float
) -> tuple[int, int, int, int]:
    """Enlarge a box by `pad` (fraction of its size) and clamp it to the image."""
    w, h = x2 - x1, y2 - y1
    return (
        max(0, int(x1 - pad * w)),
        max(0, int(y1 - pad * h)),
        min(img_w, int(x2 + pad * w)),
        min(img_h, int(y2 + pad * h)),
    )


def blur_plates(img: np.ndarray, boxes_xyxy: np.ndarray, pad: float = DEFAULT_PAD) -> np.ndarray:
    """Gaussian-blur only the region inside each (padded) box; everything else is left untouched.

    The kernel is half of the box's longer side, forced odd, so small and large plates both become unreadable.
    """
    out = img.copy()
    h_img, w_img = img.shape[:2]
    for b in boxes_xyxy:
        x1, y1, x2, y2 = padded_box(*b, w_img, h_img, pad)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        k = max(3, (max(x2 - x1, y2 - y1) // 2) | 1)
        out[y1:y2, x1:x2] = cv2.GaussianBlur(out[y1:y2, x1:x2], (k, k), 0)
    return out


def anonymize(
    path: str,
    model: Any,
    conf: float = DEFAULT_CONF,
    pad: float = DEFAULT_PAD,
    imgsz: int = DEFAULT_IMGSZ,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Detect plates in one image file and return (original, blurred, boxes)."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"cannot read image: {path}")
    boxes = detect(model, img, conf, imgsz)
    return img, blur_plates(img, boxes, pad), boxes
