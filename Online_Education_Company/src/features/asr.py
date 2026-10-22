"""Local speech-to-text fallback (faster-whisper, CPU, int8). Used only when no VTT is supplied.

Limits: no speaker labels; auto language detection is per-file, so Malayalam/English code-switching is
transcribed in the dominant language and Malayalam accuracy is noticeably lower than English.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from src.features.audio import SR, decode_mono
from src.vtt import Cue

_MODELS: dict[str, object] = {}


def transcribe_local(path: str | Path, model_size: str = "base", max_seconds: float | None = None) -> list[Cue]:
    from faster_whisper import WhisperModel

    if model_size not in _MODELS:
        _MODELS[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    model = _MODELS[model_size]
    audio = decode_mono(path, SR, max_seconds)
    segments, _info = model.transcribe(np.asarray(audio), vad_filter=True, beam_size=1, condition_on_previous_text=False)
    return [Cue(float(s.start), float(s.end), None, s.text.strip()) for s in segments if s.text.strip()]
