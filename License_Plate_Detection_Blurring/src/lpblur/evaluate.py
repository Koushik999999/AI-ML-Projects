"""Evaluation: detection metrics, recall vs confidence, recall by plate size (IoU matching at 0.5)."""

from __future__ import annotations

import os
from typing import Any, Iterator, Sequence

import numpy as np
import pandas as pd

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ
from lpblur.coords import read_gt

THRESHOLDS = (0.05, 0.10, 0.15, 0.25, 0.40, 0.50)
SIZE_BINS = (0, 20, 40, 80, 160, 5000)
SIZE_LABELS = ("< 20 px", "20-40 px", "40-80 px", "80-160 px", "> 160 px")


def iou_mat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise IoU between two sets of (x1, y1, x2, y2) boxes, shape (len(a), len(b))."""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)

    def area(z: np.ndarray) -> np.ndarray:
        return (z[:, 2] - z[:, 0]) * (z[:, 3] - z[:, 1])

    return inter / (area(a)[:, None] + area(b)[None, :] - inter)


def val_metrics(
    model: Any,
    data_yaml: str,
    split: str,
    imgsz: int = DEFAULT_IMGSZ,
    batch: int = 32,
    plots: bool = False,
    project: str = "runs/eval",
    name: str | None = None,
) -> dict[str, float]:
    """Ultralytics validation on one split; returns precision, recall, mAP@50 and mAP@50-95."""
    m = model.val(
        data=data_yaml, split=split, imgsz=imgsz, batch=batch, plots=plots, verbose=False,
        project=project, name=name or f"eval_{split}", exist_ok=True,
    )
    return dict(P=m.box.mp, R=m.box.mr, mAP50=m.box.map50, mAP50_95=m.box.map)


def predict_all(
    model: Any, root: str, split: str, conf: float, imgsz: int = DEFAULT_IMGSZ, bs: int = 64
) -> Iterator[tuple[str, tuple[int, int], np.ndarray, np.ndarray]]:
    """Yield (filename, (H, W), predicted boxes, scores) for every image of a split."""
    files = sorted(os.listdir(f"{root}/images/{split}"))
    for i in range(0, len(files), bs):
        chunk = files[i:i + bs]
        results = model.predict([f"{root}/images/{split}/{f}" for f in chunk], conf=conf, imgsz=imgsz, verbose=False)
        for f, res in zip(chunk, results):
            yield f, res.orig_shape, res.boxes.xyxy.cpu().numpy(), res.boxes.conf.cpu().numpy()


def _gt(root: str, split: str, f: str, w: int, h: int) -> np.ndarray:
    return read_gt(f"{root}/labels/{split}/{os.path.splitext(f)[0]}.txt", w, h)


def recall_vs_conf(
    model: Any,
    root: str,
    split: str,
    thresholds: Sequence[float] = THRESHOLDS,
    iou_thr: float = 0.5,
    imgsz: int = DEFAULT_IMGSZ,
) -> pd.DataFrame:
    """Plate recall (a ground-truth plate counts if a prediction matches it with IoU >= iou_thr) and false positives."""
    tp = {t: 0 for t in thresholds}
    fp = dict(tp)
    n_gt = n_img = 0
    for f, (h, w), pb, pc in predict_all(model, root, split, min(thresholds), imgsz):
        gt = _gt(root, split, f, w, h)
        n_gt += len(gt)
        n_img += 1
        for t in thresholds:
            keep = pb[pc >= t]
            m = iou_mat(gt, keep)
            tp[t] += int((m.max(axis=1) >= iou_thr).sum()) if m.size else 0
            fp[t] += len(keep) - (int((m.max(axis=0) >= iou_thr).sum()) if m.size else 0)
    return pd.DataFrame({
        "conf": list(thresholds),
        "recall": [tp[t] / n_gt for t in thresholds],
        "false_positives": [fp[t] for t in thresholds],
        "false_pos_per_image": [fp[t] / n_img for t in thresholds],
    }).round(3)


def gt_hits(
    model: Any, root: str, split: str, conf: float = DEFAULT_CONF, iou_thr: float = 0.5, imgsz: int = DEFAULT_IMGSZ
) -> pd.DataFrame:
    """One row per ground-truth plate: image name, whether it was hit, and its width in pixels."""
    rows = []
    for f, (h, w), pb, pc in predict_all(model, root, split, conf, imgsz):
        gt = _gt(root, split, f, w, h)
        m = iou_mat(gt, pb[pc >= conf])
        for j, g in enumerate(gt):
            rows.append(dict(img=f, hit=bool(m.size and m[j].max() >= iou_thr), w_px=g[2] - g[0]))
    return pd.DataFrame(rows, columns=["img", "hit", "w_px"])


def recall_by_size(hits: pd.DataFrame) -> pd.DataFrame:
    """Recall and missed-plate count per plate-width bin, from the output of `gt_hits`."""
    binned = hits.assign(**{"plate width": pd.cut(hits.w_px, list(SIZE_BINS), labels=list(SIZE_LABELS))})
    tab = binned.groupby("plate width", observed=True).hit.agg(plates="size", recall="mean").round(3)
    tab["missed"] = (tab.plates * (1 - tab.recall)).round().astype(int)
    return tab
