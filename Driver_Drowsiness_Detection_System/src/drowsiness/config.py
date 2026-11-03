"""Hyperparameters and constants. The defaults are the values used for the reported results."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CLASS_NAMES: tuple[str, str] = ("non_drowsy", "drowsy")   # list index == label; drowsy (1) is the positive class
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = REPO_ROOT / "models" / "drowsiness_float16.tflite"
DEFAULT_METADATA = REPO_ROOT / "models" / "metadata.json"
DETECTORS = ("dlib", "haar", "none")


@dataclass(frozen=True)
class Config:
    """Every tunable in one place."""

    seed: int = 42
    subset: float = 1.0            # <1.0 uses a stratified fraction of the data (smoke tests)
    detector: str = "dlib"         # dlib | haar | none (no crop, resize only)
    img_size: int = 128
    batch_size: int = 32
    val_fraction: float = 0.15     # validation share carved out of train/

    face_pad: float = 0.25         # reflect-padding added before Dlib (tight crops leave no margin for HOG)
    face_margin: float = 0.10      # extra context kept around the detected face box

    aug_rotation: float = 0.05     # fraction of a full turn -> +/- 18 degrees
    aug_zoom: float = 0.15
    aug_brightness: float = 0.25

    dropout: float = 0.3
    head_units: int = 128
    p1_epochs: int = 12            # phase 1: frozen base, train the head
    p1_lr: float = 1e-3
    p2_epochs: int = 12            # phase 2: fine-tune the last `unfreeze_last` base layers, BatchNorm frozen
    p2_lr: float = 1e-5
    unfreeze_last: int = 30
    es_patience: int = 4
    lr_patience: int = 2
    lr_factor: float = 0.3

    min_precision: float = 0.95    # validation precision floor when choosing the alert threshold
    smooth_window: int = 10        # frames averaged before an alert is raised
    n_representative: int = 200    # calibration images for full-integer quantization
