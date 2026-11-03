"""TensorFlow Lite export (float32, dynamic-range, float16, full-integer int8) and the size / accuracy / latency benchmark."""
from __future__ import annotations

import contextlib
import io
import json
import time
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

from .config import CLASS_NAMES, Config
from .data import Dataset, split_indices
from .evaluate import metrics_at
from .train import BEST_MODEL

VARIANTS = ("float32", "dynamic_range", "float16", "int8")


def _convert(saved_dir: Path, path: Path, configure: Callable[[tf.lite.TFLiteConverter], None] = lambda c: None) -> Path:
    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_dir))
    configure(converter)
    path.write_bytes(converter.convert())
    return path


def convert_all(saved_dir: Path, out_dir: Path, X_train: np.ndarray, cfg: Config) -> dict[str, Path]:
    """Convert the SavedModel into the four TFLite variants. int8 is calibrated on ``cfg.n_representative`` training images."""
    rng = np.random.default_rng(cfg.seed)

    def representative_data():
        for x in X_train[rng.choice(len(X_train), min(cfg.n_representative, len(X_train)), replace=False)]:
            yield [(x.astype("float32") / 255.0)[None]]

    def set_float16(c):
        c.optimizations = [tf.lite.Optimize.DEFAULT]
        c.target_spec.supported_types = [tf.float16]

    def set_int8(c):
        c.optimizations = [tf.lite.Optimize.DEFAULT]
        c.representative_dataset = representative_data
        c.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    configure = {"float32": lambda c: None,
                 "dynamic_range": lambda c: setattr(c, "optimizations", [tf.lite.Optimize.DEFAULT]),
                 "float16": set_float16, "int8": set_int8}
    return {name: _convert(saved_dir, out_dir / f"drowsiness_{name}.tflite", configure[name]) for name in VARIANTS}


def tflite_predict(path: Path, X: np.ndarray) -> tuple[np.ndarray, float]:
    """Run one image at a time on a single CPU thread. Returns (probabilities, mean milliseconds per image)."""
    interp = tf.lite.Interpreter(model_path=str(path), num_threads=1)
    interp.allocate_tensors()
    inp, out = interp.get_input_details()[0], interp.get_output_details()[0]
    probs = np.empty(len(X), dtype="float32")
    t0 = time.perf_counter()
    for i, x in enumerate(X):
        interp.set_tensor(inp["index"], (x.astype("float32") / 255.0)[None])
        interp.invoke()
        probs[i] = interp.get_tensor(out["index"])[0, 0]
    return probs, (time.perf_counter() - t0) / len(X) * 1000


def export(cfg: Config, ds: Dataset, out_dir: Path, bench_limit: int | None = None) -> pd.DataFrame:
    """Export the best model to TFLite, benchmark every variant on the test set and write the artefacts to ``out_dir``.

    ``bench_limit`` evaluates only the first N test images (quick checks). Writes the four ``.tflite`` files, an
    inference-only ``.keras`` file, ``tflite_comparison.csv`` and ``metadata.json`` (threshold, preprocessing, class names).
    """
    out_dir = Path(out_dir)
    best = keras.models.load_model(out_dir / BEST_MODEL, compile=False)
    tr_idx, _, te_idx = split_indices(ds, cfg)
    X_test, y_test = ds.X[te_idx][:bench_limit], ds.y[te_idx][:bench_limit]
    thr = json.loads((out_dir / "metrics.json").read_text())["threshold"] if (out_dir / "metrics.json").exists() else 0.5

    saved_dir = out_dir / "saved_model"
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):   # export logs thousands of tensor specs
        best.export(str(saved_dir))
    keras_path = out_dir / "drowsiness_model_inference.keras"   # no optimizer state: a fair size comparison
    best.save(keras_path)
    paths = convert_all(saved_dir, out_dir, ds.X[tr_idx], cfg)

    p_keras = best.predict(X_test.astype("float32") / 255.0, batch_size=128, verbose=0).ravel()
    keras_fn = tf.function(lambda x: best(x, training=False))   # graph-compiled, warmed up, default TF threading
    keras_fn(X_test[:1].astype("float32") / 255.0)
    t0 = time.perf_counter()
    n_timed = min(200, len(X_test))
    for x in X_test[:n_timed]:
        keras_fn(x.astype("float32")[None] / 255.0)
    keras_ms = (time.perf_counter() - t0) / n_timed * 1000

    m = metrics_at(y_test, p_keras, 0.5)
    rows = [dict(model="Keras (.keras)", size_KB=keras_path.stat().st_size / 1024, accuracy=m["accuracy"], precision=m["precision"], recall=m["recall"], f1=m["f1"],
                 recall_at_chosen_thr=metrics_at(y_test, p_keras, thr)["recall"], ms_per_image=keras_ms, max_abs_prob_diff_vs_keras=0.0)]
    for name, path in paths.items():
        probs, ms = tflite_predict(path, X_test)
        m = metrics_at(y_test, probs, 0.5)
        rows.append(dict(model=name, size_KB=path.stat().st_size / 1024, accuracy=m["accuracy"], precision=m["precision"], recall=m["recall"], f1=m["f1"],
                         recall_at_chosen_thr=metrics_at(y_test, probs, thr)["recall"], ms_per_image=ms,
                         max_abs_prob_diff_vs_keras=float(np.abs(probs - p_keras).max())))
    table = pd.DataFrame(rows).set_index("model")
    table["size_vs_keras"] = (table.size_KB / table.size_KB.iloc[0]).round(3)
    table.to_csv(out_dir / "tflite_comparison.csv")
    print(table.round(4).to_string())

    write_metadata(out_dir / "metadata.json", cfg, thr)
    return table


def write_metadata(path: Path, cfg: Config, threshold: float, model_file: str = "drowsiness_float16.tflite") -> None:
    """Everything an inference client needs: threshold, preprocessing recipe, class names, smoothing window."""
    meta = {"model_file": model_file, "class_names": list(CLASS_NAMES), "positive_class": CLASS_NAMES[1], "threshold": threshold,
            "img_size": cfg.img_size, "detector": cfg.detector, "face_pad": cfg.face_pad, "face_margin": cfg.face_margin,
            "interpolation": "INTER_AREA", "color_order": "RGB", "input_scaling": "uint8 / 255 -> float32 in [0, 1] (the model rescales to [-1, 1] internally)",
            "output": "sigmoid P(drowsy)", "smooth_window": cfg.smooth_window}
    Path(path).write_text(json.dumps(meta, indent=2))
