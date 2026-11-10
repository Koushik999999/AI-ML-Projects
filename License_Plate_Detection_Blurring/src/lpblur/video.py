"""Blur plates in a video file frame by frame."""

from __future__ import annotations

import time
from typing import Any

import cv2

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD
from lpblur.blur import blur_plates, detect


def blur_video(
    src: str,
    dst: str,
    model: Any,
    conf: float = DEFAULT_CONF,
    pad: float = DEFAULT_PAD,
    imgsz: int = DEFAULT_IMGSZ,
) -> tuple[int, float]:
    """Blur plates frame by frame; returns (frames written, throughput in FPS: read + detect + blur + write)."""
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open video: {src}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    n, t0 = 0, time.perf_counter()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        out.write(blur_plates(frame, detect(model, frame, conf, imgsz), pad))
        n += 1
    cap.release()
    out.release()
    return n, n / (time.perf_counter() - t0)
