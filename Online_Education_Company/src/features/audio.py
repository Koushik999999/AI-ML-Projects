"""Audio features (all local). Input is the *mixed* class audio, so these describe the room, not who spoke."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from src.media import ffmpeg_exe

SR = 16000
HOP = SR // 10  # 100 ms frames


def decode_mono(path: str | Path, sr: int = SR, max_seconds: float | None = None) -> np.ndarray:
    """Decode to float32 mono in [-1, 1] through a pipe (no temp file)."""
    cmd = [ffmpeg_exe(), "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr)]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    raw = subprocess.run(cmd + ["-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return (start, end) index pairs of consecutive True runs."""
    if not mask.any():
        return []
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def audio_features(x: np.ndarray, sr: int = SR, long_pause_s: float = 8.0) -> dict:
    n = len(x) // HOP
    if n < 20:
        return {"ok": False, "reason": "audio too short or missing"}
    fr = x[: n * HOP].reshape(n, HOP)
    rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    peak = np.abs(fr).max(axis=1)
    floor = float(np.percentile(db, 10))
    thr = max(floor + 9.0, -52.0)
    speech = db > thr
    # smooth: close gaps < 300 ms so brief consonant dips do not count as silence
    sp = speech.copy()
    for a, b in _runs(~sp):
        if b - a <= 3 and a > 0 and b < n:
            sp[a:b] = True
    dur = n / 10.0
    pauses = [(a / 10.0, b / 10.0) for a, b in _runs(~sp) if (b - a) / 10.0 >= long_pause_s]
    # digital silence (exact zeros) *inside* otherwise active audio => likely dropout, not natural quiet
    dig = peak < 1.0 / 32768
    dropouts = []
    for a, b in _runs(dig):
        L = (b - a) / 10.0
        before, after = sp[max(0, a - 10):a], sp[b:b + 10]
        if 1.0 <= L <= 30 and before.size and after.size and before.mean() > 0.3 and after.mean() > 0.3:
            dropouts.append((a / 10.0, b / 10.0))
    sp_db = db[sp]
    win = 100  # 10 s windows
    activity = [float(sp[i:i + win].mean()) for i in range(0, n, win)]
    return {
        "ok": True,
        "duration_s": dur,
        "speech_ratio": float(sp.mean()),
        "silence_ratio": float(1 - sp.mean()),
        "digital_silence_ratio": float(dig.mean()),
        "long_pauses": [{"start": s, "end": e} for s, e in pauses],
        "longest_pause_s": max([e - s for s, e in pauses], default=0.0),
        "noise_floor_db": floor,
        "median_speech_db": float(np.median(sp_db)) if sp_db.size else None,
        "p95_db": float(np.percentile(db, 95)),
        "snr_db": float(np.median(sp_db) - floor) if sp_db.size else None,
        "clipping_ratio": float((peak >= 0.99).mean()),
        "dropouts": [{"start": s, "end": e} for s, e in dropouts],
        "activity_10s": activity,
        "speech_mask_100ms": sp,  # numpy; stripped before caching
    }
