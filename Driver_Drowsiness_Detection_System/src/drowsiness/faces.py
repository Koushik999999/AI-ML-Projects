"""Face detection and cropping (Dlib HOG, OpenCV Haar cascade, or none) shared by training, prediction and the demo."""
from __future__ import annotations

import warnings
from pathlib import Path

import cv2
import numpy as np

from .config import DETECTORS

Box = tuple[int, int, int, int]   # x1, y1, x2, y2 in original image coordinates


def load_rgb(path: str | Path) -> np.ndarray:
    """Read an image file as an RGB uint8 array (OpenCV loads BGR)."""
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"cannot read image: {path}")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def crop_to_box(rgb: np.ndarray, box: Box | None, margin: float = 0.10) -> np.ndarray:
    """Crop to ``box`` plus a relative margin; fall back to the full image when no face was found."""
    if box is None:
        return rgb
    h, w = rgb.shape[:2]
    x1, y1, x2, y2 = box
    mx, my = int(margin * (x2 - x1)), int(margin * (y2 - y1))
    return rgb[max(y1 - my, 0):min(y2 + my, h), max(x1 - mx, 0):min(x2 + mx, w)]


class FaceDetector:
    """Largest-face detector with a fixed crop recipe.

    ``kind`` is ``dlib``, ``haar`` or ``none``. If ``dlib`` cannot be imported the Haar cascade is used instead and a
    warning is emitted. ``none`` never finds a face, so every image is just resized (the "no crop" ablation).
    """

    def __init__(self, kind: str = "dlib", face_pad: float = 0.25, face_margin: float = 0.10) -> None:
        if kind not in DETECTORS:
            raise ValueError(f"detector must be one of {DETECTORS}, got {kind!r}")
        self.face_pad, self.face_margin = face_pad, face_margin
        self._dlib = None
        if kind == "dlib":
            try:
                import dlib
                self._dlib = dlib.get_frontal_face_detector()
            except ImportError:
                warnings.warn("dlib is not installed; falling back to the OpenCV Haar cascade "
                              "(results will differ from the reported ones).", RuntimeWarning, stacklevel=2)
                kind = "haar"
        self.kind = kind
        self._haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") if kind == "haar" else None

    def detect(self, rgb: np.ndarray) -> Box | None:
        """Return the largest face box, or None."""
        if self.kind == "dlib":
            return self._detect_dlib(rgb)
        if self.kind == "haar":
            return self._detect_haar(rgb)
        return None

    def _detect_dlib(self, rgb: np.ndarray) -> Box | None:
        h, w = rgb.shape[:2]
        pad = int(self.face_pad * h)
        padded = cv2.copyMakeBorder(rgb, pad, pad, pad, pad, cv2.BORDER_REFLECT)   # tight crops leave HOG no context
        rects = self._dlib(padded, 0)
        if not rects:
            return None
        r = max(rects, key=lambda r: r.width() * r.height())
        return (max(r.left() - pad, 0), max(r.top() - pad, 0), min(r.right() - pad, w), min(r.bottom() - pad, h))

    def _detect_haar(self, rgb: np.ndarray) -> Box | None:
        boxes = self._haar.detectMultiScale(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), scaleFactor=1.1, minNeighbors=5)
        if len(boxes) == 0:
            return None
        x, y, w, h = max(boxes, key=lambda b: b[2] * b[3])
        return (int(x), int(y), int(x + w), int(y + h))

    def preprocess(self, rgb: np.ndarray, img_size: int = 128) -> tuple[np.ndarray, bool, float]:
        """RGB image -> (face crop resized to ``img_size`` with INTER_AREA as uint8, face found, face-box share of the image)."""
        box = self.detect(rgb)
        face = cv2.resize(crop_to_box(rgb, box, self.face_margin), (img_size, img_size), interpolation=cv2.INTER_AREA)
        area = 1.0 if box is None else (box[2] - box[0]) * (box[3] - box[1]) / (rgb.shape[0] * rgb.shape[1])
        return face, box is not None, area
