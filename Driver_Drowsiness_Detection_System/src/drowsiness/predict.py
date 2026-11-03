"""Inference with a TFLite model and its ``metadata.json``: identical preprocessing to training."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tensorflow as tf

from .config import DEFAULT_METADATA, DEFAULT_MODEL
from .faces import FaceDetector, load_rgb

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class Prediction:
    """Result for one image."""

    path: Path
    p_drowsy: float
    label: str
    threshold: float
    face_found: bool


class TFLiteClassifier:
    """A TFLite drowsiness model plus the preprocessing recipe stored next to it."""

    def __init__(self, model_path: Path = DEFAULT_MODEL, metadata_path: Path = DEFAULT_METADATA, detector: str | None = None,
                 threshold: float | None = None, num_threads: int = 1) -> None:
        self.meta = json.loads(Path(metadata_path).read_text())
        self.threshold = float(self.meta["threshold"] if threshold is None else threshold)
        self.img_size = int(self.meta["img_size"])
        self.detector = FaceDetector(detector or self.meta["detector"], self.meta["face_pad"], self.meta["face_margin"])
        self._interp = tf.lite.Interpreter(model_path=str(model_path), num_threads=num_threads)
        self._interp.allocate_tensors()
        self._in = self._interp.get_input_details()[0]
        self._out = self._interp.get_output_details()[0]

    def predict_face(self, face: np.ndarray) -> float:
        """P(drowsy) for an already cropped ``img_size`` x ``img_size`` RGB uint8 face."""
        self._interp.set_tensor(self._in["index"], (face.astype("float32") / 255.0)[None])
        self._interp.invoke()
        return float(self._interp.get_tensor(self._out["index"])[0, 0])

    def predict_rgb(self, rgb: np.ndarray) -> tuple[float, bool]:
        """Detect and crop the face (full image if none is found), then classify. Returns (P(drowsy), face found)."""
        face, found, _ = self.detector.preprocess(rgb, self.img_size)
        return self.predict_face(face), found

    def label(self, p_drowsy: float) -> str:
        """Class name for a probability at this classifier's threshold."""
        return self.meta["class_names"][int(p_drowsy >= self.threshold)]

    def predict_path(self, path: Path) -> Prediction:
        """Classify one image file."""
        p, found = self.predict_rgb(load_rgb(path))
        return Prediction(Path(path), p, self.label(p), self.threshold, found)


def collect_images(inputs: list[Path]) -> list[Path]:
    """Expand files and folders (non-recursive) into a sorted list of image files."""
    paths: list[Path] = []
    for item in map(Path, inputs):
        if item.is_dir():
            paths += sorted(p for p in item.iterdir() if p.suffix.lower() in _IMAGE_SUFFIXES)
        elif item.is_file():
            paths.append(item)
        else:
            raise FileNotFoundError(item)
    return paths
