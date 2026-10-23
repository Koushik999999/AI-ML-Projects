"""Orchestrates feature extraction for one recording. Everything runs locally; results are cached as JSON.

Order matters for the time budget: cheap audio + video analysis first, then local speech-to-text (only when no VTT was
supplied) with whatever budget remains. Every component that cannot run is recorded in `unavailable` with a reason, so the
UI can say exactly which signals are missing instead of crashing or silently guessing.
"""
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
            progress: Progress = lambda f, m: None, deadline_s: float | None = None,
            asr_model=None) -> dict:
    """Return {"media","audio","video","transcript","warnings","unavailable","elapsed_s"}.

    `whisper_model`: "tiny"/"base"/"small" or "skip". `asr_model` lets tests inject a fake model.
    Never raises for a failing optional component: that section becomes {"ok": False, "reason": ...}.
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
    unavailable: list[dict] = []

    def missing(signal: str, reason: str) -> None:
        unavailable.append({"signal": signal, "reason": reason})

    info: MediaInfo = probe(video)
    if info.duration <= 0:
        raise ValueError("Could not read this file as a video. Please upload an MP4/MOV/MKV/WEBM recording.")
    cap_s = max_minutes * 60 if max_minutes else None
    if cap_s and info.duration > cap_s:
        warnings.append(f"Recording is {info.duration / 60:.0f} min; only the first {max_minutes:.0f} min were analysed.")
    media = {"truncated": bool(cap_s and info.duration > cap_s), "duration_s": info.duration, "width": info.width, "height": info.height, "fps": info.fps,
             "audio_channels": info.audio_channels, "sample_rate": info.sample_rate,
             "has_video": info.has_video, "has_audio": info.has_audio}

    def left() -> float | None:
        return None if deadline_s is None else max(0.0, deadline_s - (time.time() - t0))

    # ---- audio ----
    progress(0.02, "Analysing audio")
    audio: dict = {"ok": False, "reason": "no audio track"}
    samples = None
    if info.has_audio:
        try:
            samples = decode_mono(video, max_seconds=cap_s)
            audio = _strip(audio_features(samples))
        except Exception as e:  # noqa: BLE001
            audio = {"ok": False, "reason": f"{type(e).__name__}"}
            missing("audio analysis (pauses, dead air, dropouts)", "the audio could not be decoded")
    else:
        missing("audio and speech", "the file has no audio track")

    # ---- video ----
    video_f: dict = {"ok": False, "reason": "skipped"}
    if info.has_video:
        if left() is not None and left() < 30:
            missing("video analysis (face, screen, camera)", "the processing time budget was already used")
        else:
            progress(0.08, "Analysing video frames")
            try:
                video_f = video_features(video, max_seconds=cap_s, progress=lambda s: progress(
                    0.08 + 0.3 * min(s / (cap_s or info.duration), 1), "Analysing video frames"))
            except Exception as e:  # noqa: BLE001
                video_f = {"ok": False, "reason": f"{type(e).__name__}"}
                missing("video analysis (face, screen, camera)", "frames could not be decoded")
    else:
        missing("video analysis (face, screen, camera)", "the file has no video track")

    # ---- transcript ----
    cues: list[Cue] = []
    source, approximate, asr_info = "none", False, {}
    if vtt:
        progress(0.4, "Reading transcript")
        cues = load_vtt(vtt)
        source = "vtt"
        if cap_s:
            cues = [c for c in cues if c.start < cap_s]
        if not cues:
            missing("transcript", "the transcript file contained no readable cues (is it a WebVTT file?)")
    elif whisper_model == "skip":
        missing("transcript and who-said-what", "transcription was switched off and no transcript was supplied")
    elif samples is None:
        missing("transcript and who-said-what", "there is no audio to transcribe")
    else:
        from src.features.asr import WhisperUnavailable, transcribe_audio
        from src.features.speakers import assign_speakers
        budget = left()
        if budget is not None and budget < 60:
            missing("transcript and who-said-what", "the processing time budget was used up by the audio/video analysis")
        else:
            try:
                res = transcribe_audio(samples, whisper_model or "tiny", deadline_s=budget, model=asr_model,
                                       progress=lambda f, m: progress(0.4 + 0.55 * f, m))
                cues, source = res.cues, "whisper"
                asr_info = {"model": res.model, "language": res.language, "covered_s": res.covered_s, "total_s": res.total_s}
                if not res.complete:
                    warnings.append(f"Time budget reached: only the first {res.covered_s / 60:.0f} of {res.total_s / 60:.0f} min were transcribed.")
                if not cues:
                    missing("transcript and who-said-what", "no speech was recognised")
                else:
                    progress(0.96, "Separating teacher and children (approximate)")
                    cues, spk = assign_speakers(samples, cues)
                    approximate = True
                    asr_info["speaker_separation"] = spk
                    warnings.append("No transcript was supplied, so it was produced by local speech recognition and teacher/children were "
                                    "separated by voice (approximate, about 70% accurate on test classes). Who-spoke-when scores are not used; "
                                    "wording, audio and video signals are.")
                    if (res.language or "en") != "en":
                        warnings.append(f"Detected language '{res.language}': recognition accuracy for this language is lower, keyword checks may miss things.")
            except WhisperUnavailable as e:
                missing("transcript and who-said-what", f"{e}")
    if source != "vtt" and source != "whisper" and not any(u["signal"].startswith("transcript") for u in unavailable):
        missing("transcript and who-said-what", "no transcript available")

    transcript = transcript_features(cues, info.duration, approximate_speakers=approximate) if cues else {"ok": False, "reason": "no transcript"}
    transcript["source"] = source
    transcript["asr"] = asr_info

    result = {"media": media, "audio": audio, "video": video_f, "transcript": transcript, "warnings": warnings,
              "unavailable": unavailable, "elapsed_s": time.time() - t0}
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(result, default=float))
    progress(1.0, "Done")
    return result
