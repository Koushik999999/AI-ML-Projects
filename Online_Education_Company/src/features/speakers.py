"""Approximate teacher/student separation for transcripts WITHOUT speaker labels (e.g. local Whisper output).

Method (all local, no model download): for every transcript segment compute a voice-timbre vector (mean
level-normalised log-mel spectrum) from the mixed class audio, run 2-means, and call the cluster holding more speech
time "Teacher" (the teacher talks most). A pitch+centroid variant was tried first and was no better than the trivial
baseline (0.63 vs 0.64 time-weighted accuracy); timbre reached 0.70 vs 0.64 (see docs/findings.md).

This is a heuristic. The recording is a mix of all participants, adults can sound like children and vice versa, and
overlapping speech is not separated. `validate_against_labels` measures it on recordings that DO have labels.
"""
from __future__ import annotations

import numpy as np

from src.features.audio import SR
from src.vtt import Cue

FRAME = int(0.04 * SR)
HOP = int(0.02 * SR)
N_BANDS = 20


def _mel_bank() -> np.ndarray:
    edges = np.linspace(0, 2595 * np.log10(1 + 7500 / 700), N_BANDS + 2)
    hz = 700 * (10 ** (edges / 2595) - 1)
    f = np.fft.rfftfreq(2 * FRAME, 1 / SR)[: FRAME + 1]
    fb = np.zeros((N_BANDS, FRAME + 1))
    for i in range(N_BANDS):
        lo, mid, hi = hz[i], hz[i + 1], hz[i + 2]
        fb[i] = np.clip(np.minimum((f - lo) / (mid - lo), (hi - f) / (hi - mid)), 0, None)
    return fb


_FB = _mel_bank()


def segment_features(x: np.ndarray, start: float, end: float) -> np.ndarray | None:
    """Voice-timbre vector: mean level-normalised log-mel spectrum of the loud frames in the span (None if too short)."""
    seg = x[int(start * SR): int(min(end, start + 20) * SR)]
    if len(seg) < FRAME * 4:
        return None
    n = (len(seg) - FRAME) // HOP
    fr = seg[np.arange(FRAME)[None, :] + HOP * np.arange(n)[:, None]]
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    fr = fr[db > -40]
    if len(fr) < 6:
        return None
    P = np.abs(np.fft.rfft(fr * np.hanning(FRAME), 2 * FRAME)[:, : FRAME + 1]) ** 2
    m = np.log(P @ _FB.T + 1e-9)
    m = m - m.mean(1, keepdims=True)  # remove loudness, keep spectral shape (timbre)
    return m.mean(0)


def _kmeans2(X: np.ndarray, iters: int = 30) -> np.ndarray:
    c = np.stack([X[0], X[np.argmax(((X - X[0]) ** 2).sum(1))]])  # farthest-point init
    lab = np.zeros(len(X), int)
    for _ in range(iters):
        d = ((X[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        new = np.stack([X[lab == k].mean(0) if (lab == k).any() else c[k] for k in (0, 1)])
        if np.allclose(new, c):
            break
        c = new
    return lab


def cluster_roles(feats: list[np.ndarray | None], durations: list[float]) -> tuple[list[str], float]:
    """Return role per segment ('Teacher'/'Student') and a separation score (between/within distance ratio)."""
    ok = [i for i, f in enumerate(feats) if f is not None]
    roles = ["Teacher"] * len(feats)
    if len(ok) < 12:
        return roles, 0.0
    X = np.stack([feats[i] for i in ok])
    Z = (X - X.mean(0)) / (X.std(0) + 1e-9)
    lab = _kmeans2(Z)
    dur = np.array([durations[i] for i in ok])
    teacher_k = int(dur[lab == 0].sum() < dur[lab == 1].sum())
    c = [Z[lab == k].mean(0) for k in (0, 1)]
    within = np.mean([np.linalg.norm(z - c[k]) for z, k in zip(Z, lab)])
    sep = float(np.linalg.norm(c[0] - c[1]) / (within + 1e-9))
    for i, k in zip(ok, lab):
        roles[i] = "Teacher" if k == teacher_k else "Student"
    return roles, sep


def assign_speakers(audio: np.ndarray, cues: list[Cue]) -> tuple[list[Cue], dict]:
    feats = [segment_features(audio, c.start, c.end) for c in cues]
    roles, sep = cluster_roles(feats, [c.end - c.start for c in cues])
    out = [Cue(c.start, c.end, r, c.text) for c, r in zip(cues, roles)]
    n_stu = sum(r == "Student" for r in roles)
    return out, {"approximate": True, "separation": sep, "student_segments": n_stu, "segments": len(cues)}


def validate_against_labels(audio: np.ndarray, labelled: list[Cue], teacher: str) -> dict:
    """Score the heuristic on cues whose true speaker is known. Baseline = call everything 'Teacher'."""
    cues = [c for c in labelled if c.end - c.start >= 0.8]
    pred, info = assign_speakers(audio, cues)
    y = np.array([c.speaker != teacher for c in cues])          # True = student
    p = np.array([c.speaker == "Student" for c in pred])
    w = np.array([c.end - c.start for c in cues])
    acc = float(((y == p) * w).sum() / w.sum())
    base = float(((~y) * w).sum() / w.sum())
    tp = float(((y & p) * w).sum())
    prec, rec = tp / max((p * w).sum(), 1e-9), tp / max((y * w).sum(), 1e-9)
    return {"time_weighted_accuracy": acc, "baseline_all_teacher": base, "student_precision": prec, "student_recall": rec,
            "separation": info["separation"], "student_share_true": float((y * w).sum() / w.sum())}
