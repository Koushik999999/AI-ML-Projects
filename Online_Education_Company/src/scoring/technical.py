"""Technical/platform issue detection, reported separately from teaching quality.

* platform faults  = things the teacher cannot control (frozen video, audio dropouts, disconnect chatter) -> never penalised;
  when they are heavy the 'Presentation' dimension is excluded from the score.
* setup issues     = teacher-controlled (camera off, dim face, nothing useful on screen) -> reported AND scored,
  because the human feedback treats them as quality factors (background, face visible, light).
"""
from __future__ import annotations


def fmt_t(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def _span(r: dict) -> str:
    return f"{fmt_t(r['start'])}-{fmt_t(r['end'])}"


def technical_report(f: dict) -> dict:
    platform: list[dict] = []
    setup: list[dict] = []
    a, v, t = f.get("audio") or {}, f.get("video") or {}, f.get("transcript") or {}
    s0, s1 = (t["session_start_s"] - 5, t["session_end_s"] + 5) if t.get("ok") else (0.0, float("inf"))
    inside = lambda r: s0 <= (r["start"] + r["end"]) / 2 <= s1  # noqa: E731 - ignore lobby / post-class footage

    if a.get("ok"):
        merged: list[dict] = []
        for d in filter(inside, a["dropouts"]):
            if merged and d["start"] - merged[-1]["end"] < 5:
                merged[-1] = {"start": merged[-1]["start"], "end": d["end"]}
            else:
                merged.append(dict(d))
        for d in merged[:3]:
            platform.append({"kind": "audio_dropout", "at": d["start"], "text": f"Audio cut out for {d['end'] - d['start']:.0f}s at {_span(d)}."})
        if a["clipping_ratio"] > 0.005:
            platform.append({"kind": "clipping", "at": None, "text": f"Audio is clipping/distorted ({a['clipping_ratio'] * 100:.1f}% of samples at full scale): microphone too hot or too close."})
        if a["median_speech_db"] is not None and a["median_speech_db"] < -38:
            setup.append({"kind": "quiet_audio", "at": None, "text": f"Voices are very quiet (median {a['median_speech_db']:.0f} dBFS); raise microphone gain."})
    elif a:
        platform.append({"kind": "no_audio", "at": None, "text": "No usable audio track was found."})

    if v.get("ok"):
        for r in [r for r in v["frozen_runs"] if inside(r)][:3]:
            platform.append({"kind": "frozen_video", "at": r["start"], "text": f"Video appears frozen for {r['end'] - r['start']:.0f}s at {_span(r)} (pixel-identical frames while a face was in view)."})
        for r in [r for r in v["camera_off_runs"] if inside(r)][:3]:
            setup.append({"kind": "camera_off", "at": r["start"], "text": f"Screen is black/camera off for {r['end'] - r['start']:.0f}s at {_span(r)}."})
        if v.get("dim_face_ratio") is not None and v["dim_face_ratio"] > 0.5 and v["face_ratio"] > 0.1:
            setup.append({"kind": "dim_face", "at": None, "text": f"Teacher's face is dim in {v['dim_face_ratio'] * 100:.0f}% of frames where it is visible: sit facing a light source."})
        if v["face_ratio"] + v["screen_ratio"] < 0.4:
            setup.append({"kind": "nothing_visible", "at": None, "text": "For most of the recording neither a face nor shared content is clearly visible."})

    if t.get("ok") and t.get("tech_chatter_count", 0) >= 8:
        ev = t["evidence"]["tech"]
        first = ev[0][0] if ev else None
        platform.append({"kind": "connection_chatter", "at": first, "text": f"{t['tech_chatter_count']} mentions of audio/video/connection problems ('can you hear me', 'unmute', 'camera'...), first around {fmt_t(first) if first is not None else '?'}."})

    # heavy = at least two *different* kinds of platform fault (e.g. dropouts + chatter about not hearing)
    heavy = len({p["kind"] for p in platform if p["kind"] in {"audio_dropout", "frozen_video", "connection_chatter", "no_audio"}}) >= 2
    return {"platform": platform, "setup": setup, "exclude_presentation": heavy}
