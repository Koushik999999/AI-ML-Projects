"""Video features, computed locally on ~1 frame / 3 s downscaled frames. Frames are never stored or exported."""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np

from src.media import ffmpeg_exe

W, H = 480, 270
STEP_S = 3.0


def iter_frames(path: str | Path, step: float = STEP_S, max_seconds: float | None = None):
    """Yield BGR frames (H, W, 3) sampled every `step` seconds, streamed from ffmpeg."""
    cmd = [ffmpeg_exe(), "-loglevel", "error", "-i", str(path), "-an", "-vf", f"fps=1/{step},scale={W}:{H}",
           "-pix_fmt", "bgr24", "-f", "rawvideo"]
    if max_seconds:
        cmd[3:3] = ["-t", str(max_seconds)]
    proc = subprocess.Popen(cmd + ["-"], stdout=subprocess.PIPE)
    size = W * H * 3
    try:
        while (buf := proc.stdout.read(size)) and len(buf) == size:
            yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    finally:
        proc.kill()


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    if not mask.any():
        return []
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def video_features(path: str | Path, step: float = STEP_S, max_seconds: float | None = None,
                   progress=None) -> dict:
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    luma, dark, diff, edge, nfaces, face_h, face_luma, hue_bg = [], [], [], [], [], [], [], []
    prev = None
    for i, f in enumerate(iter_frames(path, step, max_seconds)):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        luma.append(float(g.mean()))
        dark.append(float((g < 20).mean()))
        diff.append(float(np.abs(g.astype(np.int16) - prev).mean()) if prev is not None else 0.0)
        prev = g.astype(np.int16)
        edge.append(float((cv2.Canny(g, 80, 160) > 0).mean()))
        faces = cas.detectMultiScale(g, 1.1, 6, minSize=(22, 22))
        nfaces.append(len(faces))
        if len(faces):
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            face_h.append(h / H)
            face_luma.append(float(g[y:y + h, x:x + w].mean()))
        else:
            face_h.append(0.0)
            face_luma.append(np.nan)
        if progress and i % 50 == 0:
            progress(i * step)
    n = len(luma)
    if n < 5:
        return {"ok": False, "reason": "could not decode video frames"}
    luma, dark, diff, edge = map(np.array, (luma, dark, diff, edge))
    nfaces, face_h, face_luma = np.array(nfaces), np.array(face_h), np.array(face_luma)
    black = (luma < 12) | (dark > 0.95)
    face = nfaces > 0
    # content frames: bright, edge-rich and no face -> shared screen / board / slides
    screen = ~black & ~face & (edge > 0.02)
    changed = diff > 1.5
    # static stretches: near-identical consecutive samples for >= 60 s (not necessarily a fault: a board can be still)
    static_runs = [(a * step, b * step) for a, b in _runs(diff < 0.2) if (b - a) * step >= 60]
    # frozen candidate: camera-like (face seen nearby) but pixel-identical for >= 45 s
    frozen = [(a * step, b * step) for a, b in _runs(diff < 0.02) if (b - a) * step >= 45 and face[max(0, a - 3):b + 3].any()]
    black_runs = [(a * step, b * step) for a, b in _runs(black) if (b - a) * step >= 30]
    noface_runs = [(a * step, b * step) for a, b in _runs(~face & ~black) if (b - a) * step >= 120]
    fl = face_luma[~np.isnan(face_luma)]
    return {
        "ok": True, "step_s": step, "n_samples": n, "duration_s": n * step,
        "black_ratio": float(black.mean()), "face_ratio": float(face.mean()),
        "multi_face_ratio": float((nfaces > 1).mean()), "screen_ratio": float(screen.mean()),
        "change_rate": float(changed.mean()), "mean_diff": float(diff.mean()),
        "median_face_height_frac": float(np.median(face_h[face])) if face.any() else 0.0,
        "face_brightness": float(np.median(fl)) if fl.size else None,
        "dim_face_ratio": float((fl < 70).mean()) if fl.size else None,
        "static_runs": [{"start": a, "end": b} for a, b in static_runs],
        "frozen_runs": [{"start": a, "end": b} for a, b in frozen],
        "camera_off_runs": [{"start": a, "end": b} for a, b in black_runs],
        "no_face_runs": [{"start": a, "end": b} for a, b in noface_runs],
        "longest_static_s": max([b - a for a, b in static_runs], default=0.0),
        "series": {"face": face.astype(int).tolist(), "black": black.astype(int).tolist(),
                   "screen": screen.astype(int).tolist(), "diff": [round(float(d), 2) for d in diff]},
    }
