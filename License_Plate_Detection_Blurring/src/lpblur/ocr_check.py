"""OCR readability proxy: can EasyOCR still read a plate after blurring? (Only a proxy for a human reader.)"""

from __future__ import annotations

import os
import re
from typing import Any

import cv2
import numpy as np
import pandas as pd

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD
from lpblur.blur import anonymize
from lpblur.coords import read_gt


def make_reader(gpu: bool = False) -> Any:
    """Create an English EasyOCR reader (imports easyocr lazily; downloads models on first use)."""
    import easyocr

    return easyocr.Reader(["en"], gpu=gpu, verbose=False)


def readable(reader: Any, crop: np.ndarray, min_chars: int = 4, min_conf: float = 0.4) -> bool:
    """True if OCR returns >= min_chars letters/digits with confidence >= min_conf (crop is upscaled 3x first)."""
    if crop.shape[0] < 8 or crop.shape[1] < 8:
        return False
    crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    return any(
        c >= min_conf and len(re.sub(r"[^A-Za-z0-9]", "", t)) >= min_chars
        for _, t, c in reader.readtext(crop)
    )


def ocr_leak_check(
    model: Any,
    reader: Any,
    root: str,
    split: str,
    conf: float = DEFAULT_CONF,
    pad: float = DEFAULT_PAD,
    imgsz: int = DEFAULT_IMGSZ,
) -> dict[str, float]:
    """OCR every ground-truth plate region before and after the full pipeline.

    A missed plate stays readable, so this measures the whole system. leak_rate = readable before AND after,
    divided by readable before.
    """
    rows = []
    for f in sorted(os.listdir(f"{root}/images/{split}")):
        before, after, _ = anonymize(f"{root}/images/{split}/{f}", model, conf, pad, imgsz)
        h, w = before.shape[:2]
        gt = read_gt(f"{root}/labels/{split}/{os.path.splitext(f)[0]}.txt", w, h).astype(int)
        for x1, y1, x2, y2 in gt:
            x1, y1 = max(0, x1), max(0, y1)
            rows.append(dict(
                before=readable(reader, before[y1:y2, x1:x2]),
                after=readable(reader, after[y1:y2, x1:x2]),
            ))
    ocr = pd.DataFrame(rows, columns=["before", "after"])
    return dict(
        plates=len(ocr),
        readable_before=int(ocr.before.sum()),
        readable_after=int(ocr.after.sum()),
        leak_rate=float((ocr.before & ocr.after).sum() / max(1, ocr.before.sum())),
    )
