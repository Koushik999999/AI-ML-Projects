"""Local speech-to-text fallback (faster-whisper, CPU, int8). Used only when no VTT is supplied.

Design:
* the audio is processed in fixed windows (default 5 min) so progress can be reported and a time budget enforced;
* if the budget is hit, the transcript so far is returned with `covered_s` < duration (the caller warns);
* if the model cannot be loaded (no network, no disk, missing package) `WhisperUnavailable` is raised with a readable reason.

Limits: no speaker labels (see src/features/speakers.py); auto language detection is per window, so Malayalam/English
code-switching is transcribed in the dominant language and Malayalam accuracy is clearly worse than English.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from src.features.audio import SR
from src.vtt import Cue

_MODELS: dict[str, object] = {}
WINDOW_S = 300.0
OVERLAP_S = 2.0


class WhisperUnavailable(RuntimeError):
    """Raised when local transcription cannot run; the message is safe to show to the user."""


@dataclass
class AsrResult:
    cues: list[Cue]
    covered_s: float      # seconds of audio actually transcribed
    total_s: float
    language: str | None
    model: str

    @property
    def complete(self) -> bool:
        return self.covered_s >= self.total_s - 1.0


def model_dir() -> str | None:
    return os.environ.get("MODEL_DIR") or None


def load_model(model_size: str = "tiny"):
    """Load (and memoise) a faster-whisper model. Also used at app start to warm the cache."""
    if model_size in _MODELS:
        return _MODELS[model_size]
    try:
        from faster_whisper import WhisperModel
    except Exception as e:  # noqa: BLE001
        raise WhisperUnavailable(f"faster-whisper is not installed ({type(e).__name__}).") from e
    try:
        m = WhisperModel(model_size, device="cpu", compute_type="int8", download_root=model_dir(),
                         cpu_threads=int(os.environ.get("WHISPER_THREADS", "0")) or 0)
    except Exception as e:  # noqa: BLE001 - network, disk, corrupt cache...
        raise WhisperUnavailable(f"the '{model_size}' speech model could not be loaded ({type(e).__name__}); "
                                 "it is downloaded on first use and the host may be offline.") from e
    _MODELS[model_size] = m
    return m


def transcribe_audio(audio: np.ndarray, model_size: str = "tiny", *, deadline_s: float | None = None,
                     progress: Callable[[float, str], None] = lambda f, m: None, model=None,
                     window_s: float = WINDOW_S) -> AsrResult:
    """Transcribe a 16 kHz mono float array in windows. `model` is injectable for tests."""
    model = model or load_model(model_size)
    total = len(audio) / SR
    t0 = time.time()
    cues: list[Cue] = []
    language: str | None = None
    pos = 0.0
    while pos < total:
        if deadline_s is not None and time.time() - t0 > deadline_s:
            break
        end = min(total, pos + window_s)
        seg = audio[int(pos * SR): int((end + OVERLAP_S) * SR)]
        progress(min(pos / total, 1.0), f"Transcribing locally ({model_size}): {pos / 60:.0f}-{end / 60:.0f} of {total / 60:.0f} min")
        try:
            segments, info = model.transcribe(np.asarray(seg, dtype=np.float32), vad_filter=True, beam_size=1,
                                              condition_on_previous_text=False)
            language = language or getattr(info, "language", None)
            for s in segments:
                text = s.text.strip()
                start = pos + float(s.start)
                if text and start < end:  # the 2 s overlap is only context; avoid duplicates
                    cues.append(Cue(start, pos + float(s.end), None, text))
        except Exception as e:  # noqa: BLE001
            if not cues:
                raise WhisperUnavailable(f"transcription failed ({type(e).__name__}).") from e
            break
        pos = end
    return AsrResult(cues, min(pos, total), total, language, model_size)
