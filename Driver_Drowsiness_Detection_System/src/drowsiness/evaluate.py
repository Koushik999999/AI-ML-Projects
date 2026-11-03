"""Metrics, validation-set threshold selection and the one-time test-set evaluation."""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from tensorflow import keras

from . import plots
from .config import Config
from .data import Dataset, make_dataset, split_indices
from .train import BEST_MODEL


def metrics_at(y: np.ndarray, p: np.ndarray, thr: float) -> dict[str, float]:
    """Accuracy, precision, recall, F1 and confusion counts (Drowsy = positive) when predicting ``p >= thr``."""
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(threshold=thr, accuracy=accuracy_score(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred), f1=f1_score(y, pred), TP=tp, FN=fn, FP=fp, TN=tn)


def select_threshold(y_val: np.ndarray, p_val: np.ndarray, min_precision: float = 0.95) -> tuple[float, pd.DataFrame]:
    """Threshold on a 0.01 grid that maximises validation recall subject to precision >= ``min_precision``; ties -> highest.

    Returns ``(threshold, sweep)``. If no threshold reaches the precision floor (only possible for a badly under-trained
    model, e.g. in smoke tests) the threshold with the best precision is used instead, with a warning.
    """
    grid = np.round(np.arange(0.01, 1.00, 0.01), 2)
    sweep = pd.DataFrame([metrics_at(y_val, p_val, t) for t in grid])
    eligible = sweep[sweep.precision >= min_precision]
    if eligible.empty:
        warnings.warn(f"no threshold reaches validation precision >= {min_precision:.0%}; using the most precise one", RuntimeWarning, stacklevel=2)
        return float(sweep[sweep.precision == sweep.precision.max()].threshold.max()), sweep
    return float(eligible[eligible.recall == eligible.recall.max()].threshold.max()), sweep


def evaluate(cfg: Config, ds: Dataset, out_dir: Path) -> dict:
    """Reload the best checkpoint, choose the threshold on validation, then evaluate once on the test set.

    The test set is never used to select anything. Writes ``metrics.json``, ``final_results.csv``,
    ``threshold_sweep.csv`` and figures (test evaluation, threshold sweep, error examples) into ``out_dir``.
    """
    out_dir = Path(out_dir)
    model = keras.models.load_model(out_dir / BEST_MODEL, compile=False)
    _, va_idx, te_idx = split_indices(ds, cfg)
    y_val, y_test = ds.y[va_idx], ds.y[te_idx]
    p_val = model.predict(make_dataset(ds.X[va_idx], y_val, cfg, training=False), verbose=0).ravel()
    p_test = model.predict(make_dataset(ds.X[te_idx], y_test, cfg, training=False), verbose=0).ravel()

    thr, sweep = select_threshold(y_val, p_val, cfg.min_precision)
    sweep.to_csv(out_dir / "threshold_sweep.csv", index=False)
    plots.threshold_sweep(sweep, thr, cfg.min_precision, out_dir / "threshold_sweep.png")
    print(f"Chosen threshold: {thr} (validation, max recall with precision >= {cfg.min_precision:.0%}; ties -> highest)")

    print(classification_report(y_test, (p_test >= 0.5).astype(int), target_names=["Non-Drowsy (0)", "Drowsy (1)"], digits=4))
    roc_auc, ap = plots.test_evaluation(y_test, p_test, 0.5, out_dir / "test_evaluation.png")
    final = pd.DataFrame({"Keras @ 0.5": metrics_at(y_test, p_test, 0.5),
                          f"Keras @ {thr} (chosen on val)": metrics_at(y_test, p_test, thr)}).T[["accuracy", "precision", "recall", "f1", "TP", "FN", "FP", "TN"]]
    final.to_csv(out_dir / "final_results.csv")
    print(final.round(4).to_string())

    _save_error_examples(ds, te_idx, p_test, thr, out_dir)
    result = {"threshold": thr, "min_precision": cfg.min_precision, "roc_auc": float(roc_auc), "average_precision": float(ap),
              "test_at_0.5": {k: float(v) for k, v in metrics_at(y_test, p_test, 0.5).items()},
              "test_at_threshold": {k: float(v) for k, v in metrics_at(y_test, p_test, thr).items()}}
    (out_dir / "metrics.json").write_text(json.dumps(result, indent=2))
    np.save(out_dir / "test_probabilities.npy", p_test)
    return result


def _save_error_examples(ds: Dataset, te_idx: np.ndarray, p_test: np.ndarray, thr: float, out_dir: Path, n: int = 12) -> None:
    """Figures of the most confidently wrong test images (false negatives and false positives)."""
    test_df = ds.df.iloc[te_idx].reset_index(drop=True).assign(p_drowsy=p_test)
    test_df["pred"] = (p_test >= thr).astype(int)
    groups = {"false_negatives": (test_df[(test_df.label == 1) & (test_df.pred == 0)].sort_values("p_drowsy"), "False negatives: drowsy faces classified as alert (most confidently wrong first)"),
              "false_positives": (test_df[(test_df.label == 0) & (test_df.pred == 1)].sort_values("p_drowsy", ascending=False), "False positives: alert faces classified as drowsy (most confidently wrong first)")}
    print(f"At threshold {thr}: {len(groups['false_negatives'][0])} false negatives, {len(groups['false_positives'][0])} false positives")
    for name, (errors, title) in groups.items():
        top = errors.head(n)
        if top.empty:
            continue
        plots.image_grid([ds.X[te_idx[i]] for i in top.index], [f"{Path(r.path).name}\nP(drowsy)={r.p_drowsy:.2f}" for r in top.itertuples()],
                         ncols=6, suptitle=title, path=out_dir / f"{name}.png")
