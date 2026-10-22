"""Orchestrates feature extraction for one recording. Everything runs locally; results are cached as JSON."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable

from src.features.audio import audio_features, decode_mono
from src.features.transcript import transcript_features
from src.features.video import video_features
from src.media import MediaInfo, probe
from src.vtt import Cue, load_vtt

CACHE_DIR = Path(os.environ.get("CACHE_DIR", "cache"))
Progress = Callable[[float, str], None]


def file_key(path: str | Path, extra: str = "") -> str:
    """Cheap content fingerprint: size + first/last 1 MB (fast on multi-GB files)."""
    p = Path(path)
    h = hashlib.sha256(extra.encode())
    h.update(str(p.stat().st_size).encode())
    with p.open("rb") as fh:
        h.update(fh.read(1 << 20))
        fh.seek(max(0, p.stat().st_size - (1 << 20)))
        h.update(fh.read(1 << 20))
    return h.hexdigest()[:16]


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("speech_mask")}


def analyze(video: str | Path, vtt: str | Path | None = None, *, use_cache: bool = True,
            max_minutes: float | None = None, whisper_model: str | None = None,
            progress: Progress = lambda f, m: None, deadline_s: float | None = None) -> dict:
    """Return {"media":..., "audio":..., "video":..., "transcript":..., "warnings": [...]}.

    Never raises for a bad optional component: the failing section gets {"ok": False, "reason": ...}
    and a warning, so the app can still score with what it has.
    """
    t0 = time.time()
    video = Path(video)
    if not video.is_file():
        raise ValueError("Could not find the recording file.")
    key = file_key(video, extra=f"{Path(vtt).stat().st_size if vtt else 'novtt'}|{max_minutes}|{whisper_model}")
    cache_file = CACHE_DIR / f"features_{key}.json"
    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text())

    warnings: list[str] = []
    info: MediaInfo = probe(video)
    if info.duration <= 0:
        raise ValueError("Could not read this file as a video. Please upload an MP4/MOV/MKV/WEBM recording.")
    cap_s = max_minutes * 60 if max_minutes else None
    if cap_s and info.duration > cap_s:
        warnings.append(f"Recording is {info.duration / 60:.0f} min; only the first {max_minutes:.0f} min were analysed.")
    media = {"duration_s": info.duration, "width": info.width, "height": info.height, "fps": info.fps,
             "audio_channels": info.audio_channels, "sample_rate": info.sample_rate,
             "has_video": info.has_video, "has_audio": info.has_audio}

    def over() -> bool:
        return bool(deadline_s and time.time() - t0 > deadline_s)

    # ---- transcript ----
    progress(0.02, "Reading transcript")
    cues: list[Cue] = []
    transcript_source = "none"
    if vtt:
        cues = load_vtt(vtt)
        transcript_source = "vtt"
        if cap_s:
            cues = [c for c in cues if c.start < cap_s]  # keep transcript consistent with the analysed window
        if not cues:
            warnings.append("The transcript file contained no readable cues (is it a WebVTT file?).")
    elif info.has_audio and whisper_model != "skip":
        progress(0.05, "No transcript supplied: transcribing locally (slow)")
        try:
            from src.features.asr import transcribe_local
            cues = transcribe_local(video, model_size=whisper_model or "base", max_seconds=cap_s)
            transcript_source = "whisper"
            warnings.append("Transcript produced by local Whisper: no speaker labels, so teacher/student split is unavailable; "
                            "Malayalam/English code-switching accuracy is limited.")
        except Exception as e:  # noqa: BLE001
            warnings.append(f"Local transcription failed ({type(e).__name__}); scored without transcript features.")
    else:
        warnings.append("No transcript supplied and transcription skipped; interaction features are unavailable.")
    transcript = transcript_features(cues, info.duration) if cues else {"ok": False, "reason": "no transcript"}
    transcript["source"] = transcript_source

    # ---- audio ----
    progress(0.15, "Analysing audio")
    audio: dict = {"ok": False, "reason": "no audio track"}
    if info.has_audio:
        try:
            audio = _strip(audio_features(_decode(video, cap_s)))
        except Exception as e:  # noqa: BLE001
            audio = {"ok": False, "reason": f"{type(e).__name__}: {e}"}
            warnings.append("Audio analysis failed.")
    else:
        warnings.append("No audio track found in the recording.")

    # ---- video ----
    video_f: dict = {"ok": False, "reason": "skipped"}
    if info.has_video and not over():
        progress(0.3, "Analysing video frames")
        try:
            video_f = video_features(video, max_seconds=cap_s,
                                     progress=lambda s: progress(0.3 + 0.65 * min(s / (cap_s or info.duration), 1), "Analysing video frames"))
        except Exception as e:  # noqa: BLE001
            video_f = {"ok": False, "reason": f"{type(e).__name__}: {e}"}
            warnings.append("Video analysis failed.")
    elif over():
        warnings.append("Time budget reached: video analysis skipped.")

    result = {"media": media, "audio": audio, "video": video_f, "transcript": transcript, "warnings": warnings,
              "elapsed_s": time.time() - t0}
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(result, default=float))
    progress(1.0, "Done")
    return result


def _decode(video: Path, cap_s: float | None):
    return decode_mono(video, max_seconds=cap_s)
