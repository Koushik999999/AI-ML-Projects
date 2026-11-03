"""Figure helpers (matplotlib, saved to files; no interactive display)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402
import seaborn as sns             # noqa: E402
from sklearn.metrics import auc, average_precision_score, confusion_matrix, precision_recall_curve, roc_curve   # noqa: E402


def _save(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close()


def training_curves(hist: pd.DataFrame, boundary: float, path: Path) -> None:
    """Loss, accuracy and recall per epoch (train vs validation); the dashed line marks the start of phase 2."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    for ax, (metric, title) in zip(axes, (("loss", "Loss"), ("accuracy", "Accuracy"), ("recall", "Recall (Drowsy)"))):
        ax.plot(hist.index, hist[metric], label="train", marker="o", ms=3)
        ax.plot(hist.index, hist[f"val_{metric}"], label="validation", marker="o", ms=3)
        ax.axvline(boundary, color="grey", ls="--")
        ax.set_title(title); ax.set_xlabel("epoch"); ax.legend()
    _save(path)


def test_evaluation(y: np.ndarray, p: np.ndarray, thr: float, path: Path) -> tuple[float, float]:
    """Confusion matrix, ROC and precision-recall curves on the test set. Returns (ROC AUC, average precision)."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.3))
    cm = confusion_matrix(y, (p >= thr).astype(int))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axes[0], xticklabels=["Non-Drowsy", "Drowsy"], yticklabels=["Non-Drowsy", "Drowsy"])
    axes[0].set_xlabel("Predicted"); axes[0].set_ylabel("Actual"); axes[0].set_title(f"Confusion matrix (test, threshold {thr})")
    fpr, tpr, _ = roc_curve(y, p); roc_auc = auc(fpr, tpr)
    axes[1].plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}"); axes[1].plot([0, 1], [0, 1], "k--", lw=1)
    axes[1].set_xlabel("False positive rate"); axes[1].set_ylabel("True positive rate (recall)"); axes[1].set_title("ROC curve (test)"); axes[1].legend()
    prec, rec, _ = precision_recall_curve(y, p); ap = average_precision_score(y, p)
    axes[2].plot(rec, prec, label=f"AP = {ap:.4f}"); axes[2].set_xlabel("Recall"); axes[2].set_ylabel("Precision")
    axes[2].set_title("Precision-recall curve (test)"); axes[2].legend(loc="lower left")
    _save(path)
    return roc_auc, ap


def threshold_sweep(sweep: pd.DataFrame, chosen: float, min_precision: float, path: Path) -> None:
    """Validation precision / recall / F1 / accuracy against the threshold."""
    fig, ax = plt.subplots(figsize=(8, 4))
    for col in ("precision", "recall", "f1", "accuracy"):
        ax.plot(sweep.threshold, sweep[col], label=col)
    ax.axvline(chosen, color="k", ls="--", label=f"chosen = {chosen}"); ax.axvline(0.5, color="grey", ls=":", label="default 0.5")
    ax.axhline(min_precision, color="red", lw=0.6, label="min precision")
    ax.set_ylim(0.9, 1.005); ax.set_xlabel("threshold"); ax.set_ylabel("score (validation)"); ax.set_title("Threshold sweep on the validation set"); ax.legend()
    _save(path)


def image_grid(images: list[np.ndarray], titles: list[str], ncols: int, suptitle: str, path: Path, cell: tuple[float, float] = (2.2, 2.5)) -> None:
    """Grid of small images with titles."""
    nrows = int(np.ceil(len(images) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(cell[0] * ncols, cell[1] * nrows), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, img, title in zip(axes.ravel(), images, titles):
        ax.imshow(img); ax.set_title(title, fontsize=8)
    fig.suptitle(suptitle, y=1.0)
    _save(path)
