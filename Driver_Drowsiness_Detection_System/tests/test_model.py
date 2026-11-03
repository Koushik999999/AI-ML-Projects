"""Architecture, fine-tuning switch and TFLite round trip (random weights, no downloads)."""
import json

import numpy as np
import pytest
import tensorflow as tf
from tensorflow import keras

from drowsiness.config import Config
from drowsiness.model import build_model, unfreeze_top_layers
from drowsiness.predict import TFLiteClassifier


@pytest.fixture(scope="module")
def built():
    return build_model(Config(), weights=None)


def _trainable(model):
    return sum(int(np.prod(w.shape)) for w in model.trainable_weights)


def test_parameter_counts(built):
    model, base = built
    assert model.count_params() == 2_422_081
    assert base.count_params() == 2_257_984 and len(base.layers) == 154
    assert _trainable(model) == 164_097   # head only (phase 1)


def test_phase2_unfreezes_30_layers_but_keeps_batchnorm_frozen(built):
    model, base = built
    unfreeze_top_layers(base, 30)
    assert _trainable(model) == 1_674_817
    assert not any(layer.trainable for layer in base.layers if isinstance(layer, keras.layers.BatchNormalization))
    assert not any(layer.trainable for layer in base.layers[:-30])


def test_output_is_a_probability(built):
    model, _ = built
    p = model(np.random.default_rng(0).random((3, 128, 128, 3), dtype=np.float32)).numpy()
    assert p.shape == (3, 1) and ((p >= 0) & (p <= 1)).all()


def test_tiny_model_converts_to_tflite_and_runs(tmp_path):
    tiny = keras.Sequential([keras.Input((128, 128, 3)), keras.layers.GlobalAveragePooling2D(), keras.layers.Dense(1, activation="sigmoid")])
    tiny.export(str(tmp_path / "saved_model"))   # same route as the real export: SavedModel -> TFLite (Keras 3)
    tflite = tmp_path / "tiny.tflite"
    tflite.write_bytes(tf.lite.TFLiteConverter.from_saved_model(str(tmp_path / "saved_model")).convert())
    meta = tmp_path / "metadata.json"
    meta.write_text(json.dumps({"class_names": ["non_drowsy", "drowsy"], "threshold": 0.5, "img_size": 128, "detector": "none",
                                "face_pad": 0.25, "face_margin": 0.1}))
    clf = TFLiteClassifier(tflite, meta)
    face = np.random.default_rng(0).integers(0, 256, (128, 128, 3), dtype=np.uint8)
    p = clf.predict_face(face)
    assert 0.0 <= p <= 1.0
    assert p == pytest.approx(float(tiny(face[None].astype("float32") / 255.0).numpy()[0, 0]), abs=1e-4)
    assert clf.label(0.9) == "drowsy" and clf.label(0.1) == "non_drowsy"
