"""Preprocessing shape/dtype/range and the crop recipe (synthetic images, no dataset)."""
import sys

import numpy as np
import pandas as pd
import pytest

from drowsiness.config import Config
from drowsiness.data import make_dataset, subsample
from drowsiness.faces import FaceDetector, crop_to_box


def _image(h=227, w=227, seed=0):
    return np.random.default_rng(seed).integers(0, 256, (h, w, 3), dtype=np.uint8)


def test_no_detector_resizes_only():
    face, found, area = FaceDetector("none").preprocess(_image(), 128)
    assert face.shape == (128, 128, 3) and face.dtype == np.uint8
    assert found is False and area == 1.0


def test_dlib_falls_back_to_the_resized_original_when_no_face():
    pytest.importorskip("dlib")
    img = np.full((227, 227, 3), 128, dtype=np.uint8)   # a flat image contains no face
    face, found, _ = FaceDetector("dlib").preprocess(img, 128)
    expected, _, _ = FaceDetector("none").preprocess(img, 128)
    assert not found
    assert np.array_equal(face, expected)


def test_missing_dlib_falls_back_to_haar_with_a_warning(monkeypatch):
    monkeypatch.setitem(sys.modules, "dlib", None)   # makes `import dlib` raise ImportError
    with pytest.warns(RuntimeWarning, match="Haar"):
        detector = FaceDetector("dlib")
    assert detector.kind == "haar"
    face, _, _ = detector.preprocess(_image(), 128)
    assert face.shape == (128, 128, 3)


def test_unknown_detector_is_rejected():
    with pytest.raises(ValueError):
        FaceDetector("mtcnn")


def test_crop_to_box_adds_margin_and_clips_to_the_image():
    img = _image(100, 100)
    crop = crop_to_box(img, (20, 20, 60, 60), margin=0.10)   # 40 px box -> 4 px margin on each side
    assert crop.shape == (48, 48, 3)
    assert crop_to_box(img, (0, 0, 100, 100), margin=0.10).shape == (100, 100, 3)
    assert crop_to_box(img, None) is img


def test_dataset_batches_are_float32_in_unit_range():
    X = np.random.default_rng(1).integers(0, 256, (10, 128, 128, 3), dtype=np.uint8)
    y = np.array([0, 1] * 5)
    cfg = Config(batch_size=4)
    xb, _ = next(iter(make_dataset(X, y, cfg, training=False)))
    assert xb.shape == (4, 128, 128, 3) and xb.dtype.name == "float32"
    assert 0.0 <= float(xb.numpy().min()) and float(xb.numpy().max()) <= 1.0
    xt, _ = next(iter(make_dataset(X, y, cfg, training=True)))   # augmentation keeps the range
    assert 0.0 <= float(xt.numpy().min()) and float(xt.numpy().max()) <= 1.0


def test_subsample_is_stratified_and_deterministic():
    df = pd.DataFrame({"split": ["train"] * 60 + ["test"] * 40, "label": [0, 1] * 50})
    a, b = subsample(df, 0.5, seed=1), subsample(df, 0.5, seed=1)
    assert a.equals(b)
    assert sorted(a.groupby(["split", "label"]).size().tolist()) == [10, 10, 15, 15]
    assert subsample(df, 1.0, seed=1) is df
