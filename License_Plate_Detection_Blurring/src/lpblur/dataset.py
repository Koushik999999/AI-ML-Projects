"""Dataset audit, cleaning and train/val leakage detection for a YOLO-format dataset.

Expected layout: ``<root>/images/<split>/*.jpg`` and ``<root>/labels/<split>/*.txt``.
"""

from __future__ import annotations

import os
import re
import shutil
from collections import Counter
from typing import Sequence

import pandas as pd
from PIL import Image

SPLITS = ("train", "val", "test")
_MISSING_LABEL = ("no label file", "empty label file")


def base_name(filename: str) -> str:
    """Source-photo name of an image: strips the Roboflow ``_jpg.rf.<hash>`` augmentation suffix."""
    m = re.match(r"^(.*?)_(?:jpg|jpeg|png)\.rf\.", filename, re.I)
    return m.group(1) if m else os.path.splitext(filename)[0]


def audit_dataset(
    root: str, splits: Sequence[str] = SPLITS
) -> tuple[pd.DataFrame, list[tuple[str, str, str]], Counter]:
    """Read every image and label once.

    Returns (plates dataframe, problems, columns-per-label-line counter). The dataframe has one row per plate
    with normalised and pixel geometry; problems are (split, image, reason) for missing, empty or malformed labels.
    """
    rows: list[dict] = []
    problems: list[tuple[str, str, str]] = []
    col_counts: Counter = Counter()
    for s in splits:
        for img in os.listdir(f"{root}/images/{s}"):
            stem = os.path.splitext(img)[0]
            lp = f"{root}/labels/{s}/{stem}.txt"
            with Image.open(f"{root}/images/{s}/{img}") as im:
                w, h = im.size
            if not os.path.exists(lp):
                problems.append((s, img, "no label file"))
                continue
            with open(lp) as fh:
                lines = [ln.split() for ln in fh.read().strip().splitlines() if ln.strip()]
            if not lines:
                problems.append((s, img, "empty label file"))
                continue
            for p in lines:
                col_counts[len(p)] += 1
                if len(p) < 5:
                    problems.append((s, img, "malformed line"))
                    continue
                cls, (cx, cy, bw, bh) = int(float(p[0])), map(float, p[1:5])
                rows.append(dict(split=s, img=img, W=w, H=h, cls=cls, cx=cx, cy=cy, w=bw, h=bh))

    df = pd.DataFrame(rows, columns=["split", "img", "W", "H", "cls", "cx", "cy", "w", "h"])
    df["w_px"], df["h_px"] = df.w * df.W, df.h * df.H
    df["area_pct"] = df.w * df.h * 100
    df["aspect"] = df.w_px / df.h_px
    return df, problems, col_counts


def source_bases(df: pd.DataFrame, splits: Sequence[str] = SPLITS) -> dict[str, set[str]]:
    """Set of source-photo names per split, from the audited dataframe."""
    imgs = df.drop_duplicates(["split", "img"])
    return {s: set(imgs[imgs.split == s].img.map(base_name)) for s in splits}


def find_leakage(bases: dict[str, set[str]]) -> dict[str, set[str]]:
    """Source photos shared between each pair of splits (augmented copies leaking across splits)."""
    return {
        "train&val": bases["train"] & bases["val"],
        "train&test": bases["train"] & bases["test"],
        "val&test": bases["val"] & bases["test"],
    }


def _move_out(root: str, removed: str, split: str, img: str) -> None:
    stem = os.path.splitext(img)[0]
    for k, name in (("images", img), ("labels", stem + ".txt")):
        src = f"{root}/{k}/{split}/{name}"
        if os.path.exists(src):
            os.makedirs(f"{removed}/{k}/{split}", exist_ok=True)
            shutil.move(src, f"{removed}/{k}/{split}/{name}")


def write_data_yaml(root: str) -> str:
    """Write ``<root>/data.yaml`` (single class: license_plate) with an absolute dataset path; returns its path."""
    path = os.path.join(root, "data.yaml")
    with open(path, "w") as fh:
        fh.write(
            f"path: {os.path.abspath(root)}\ntrain: images/train\nval: images/val\ntest: images/test\n"
            "names:\n  0: license_plate\n"
        )
    return path


def clean_dataset(root: str, removed: str, splits: Sequence[str] = SPLITS) -> dict[str, int]:
    """Move (never delete) images with missing or empty labels and val images whose source photo is in train.

    Moved files go to ``removed`` with the same images/labels/<split> layout. Returns counts of what was moved.
    """
    df, problems, _ = audit_dataset(root, splits)
    bases = source_bases(df, splits)
    n_missing = n_leak = 0
    for s, img, reason in problems:
        if reason in _MISSING_LABEL:
            _move_out(root, removed, s, img)
            n_missing += 1
    leak = bases["train"] & bases["val"]
    for f in os.listdir(f"{root}/images/val"):
        if base_name(f) in leak:
            _move_out(root, removed, "val", f)
            n_leak += 1
    return {"missing_or_empty_label": n_missing, "val_leaked_from_train": n_leak}
