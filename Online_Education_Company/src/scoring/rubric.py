"""Transparent weighted rubric. Dimensions come from the human feedback notes (feedbacks.pdf), not generic ideas:
rapport/intro, individual one-to-one interaction, energetic & pleasant tone, structure (checks, recap, closing, homework),
pacing, and presentation (visible, lit, camera on). Every number below is a *reasoned* range, not fitted to the 8 labels.

Each item is (feature path, lo, hi, weight): value is ramped linearly to 0..1 between lo (bad) and hi (good);
lo > hi means "lower is better". Missing features are skipped and the dimension is re-normalised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

LABELS = ["Poor", "Average", "Good", "Excellent"]


def ramp(x: float | None, lo: float, hi: float) -> float | None:
    """Linear 0..1 score; works for lo>hi (lower is better). None stays None."""
    if x is None:
        return None
    if lo == hi:
        return 1.0 if x >= hi else 0.0
    return min(1.0, max(0.0, (x - lo) / (hi - lo)))


def band(x: float | None, lo: float, ideal_lo: float, ideal_hi: float, hi: float) -> float | None:
    """1.0 inside [ideal_lo, ideal_hi], falling linearly to 0 at lo / hi."""
    if x is None:
        return None
    if ideal_lo <= x <= ideal_hi:
        return 1.0
    return ramp(x, lo, ideal_lo) if x < ideal_lo else ramp(x, hi, ideal_hi)


def flag(v: Any) -> float | None:
    return None if v is None else (1.0 if v else 0.0)


@dataclass(frozen=True)
class Item:
    name: str
    get: Callable[[dict], float | None]   # returns a 0..1 score or None when unavailable
    weight: float
    why: str


def _t(f: dict, k: str):  # transcript feature
    t = f.get("transcript") or {}
    return t.get(k) if t.get("ok") and t.get("has_speakers", True) else None


def _lex(f: dict, k: str):
    """Keyword-derived transcript feature; unavailable when the transcript is not mostly English (garbled ASR)."""
    t = f.get("transcript") or {}
    return _t(f, k) if t.get("lexicon_reliable", True) else None


def _a(f: dict, k: str):
    a = f.get("audio") or {}
    return a.get(k) if a.get("ok") else None


def _v(f: dict, k: str):
    v = f.get("video") or {}
    return v.get(k) if v.get("ok") else None


def _pauses_per_hour(f: dict) -> float | None:
    a, t = f.get("audio") or {}, f.get("transcript") or {}
    if not a.get("ok"):
        return None
    s, e = (t.get("session_start_s", 0.0), t.get("session_end_s", a["duration_s"])) if t.get("ok") else (0.0, a["duration_s"])
    inside = [p for p in a["long_pauses"] if p["start"] >= s - 1 and p["end"] <= e + 1]
    return len(inside) / max((e - s) / 3600, 0.1)


def _visual_content(f: dict) -> float | None:
    v = f.get("video") or {}
    return min(1.0, v["face_ratio"] + v["screen_ratio"]) if v.get("ok") else None


DIMENSIONS: dict[str, dict] = {
    "Rapport & opening": {"weight": 0.15, "items": [
        Item("rapport question in opening", lambda f: flag(_lex(f, "has_rapport")), 0.45, "teacher asks the children how they are/how their day was in the first minutes"),
        Item("greeting", lambda f: flag(_lex(f, "has_greeting")), 0.25, "class opens with a greeting"),
        Item("new-joiner introduction", lambda f: flag(_lex(f, "has_new_joiner_intro")), 0.30, "children get time to introduce themselves"),
    ]},
    "Individual interaction": {"weight": 0.28, "items": [
        Item("children asked individually", lambda f: ramp(_t(f, "n_students_asked_individually"), 1, 6), 0.30, "distinct children who answer a direct question"),
        Item("student turns per minute", lambda f: ramp(_t(f, "student_turns_per_min"), 2.0, 8.0), 0.30, "how often children speak"),
        Item("participation spread", lambda f: ramp(_t(f, "student_top_share"), 0.75, 0.35), 0.20, "one child should not dominate"),
        Item("response latency", lambda f: ramp(_t(f, "median_response_latency_s"), 2.0, 0.6), 0.20, "children answer quickly when engaged"),
    ]},
    "Energy & positivity": {"weight": 0.15, "items": [
        Item("praise rate", lambda f: ramp(_lex(f, "praise_per_10min"), 1.0, 8.0), 0.6, "praise / encouragement per 10 min"),
        Item("energetic wording", lambda f: ramp(_lex(f, "energy_marks_per_min"), 0.1, 0.7), 0.4, "exclamations and enthusiastic words"),
    ]},
    "Structure & clarity": {"weight": 0.17, "items": [
        Item("checks understanding", lambda f: ramp(_lex(f, "check_per_10min"), 3.0, 10.0), 0.25, "'understood?' / 'any doubt?' per 10 min"),
        Item("homework given", lambda f: flag(_lex(f, "has_homework")), 0.25, "homework is assigned"),
        Item("recap", lambda f: flag(_lex(f, "has_recap")), 0.20, "lesson is summarised near the end"),
        Item("closing", lambda f: flag(_lex(f, "has_closing")), 0.15, "proper conclusion / goodbye"),
        Item("no long teacher monologue", lambda f: ramp(_t(f, "longest_monologue_s"), 600, 120), 0.15, "longest uninterrupted teacher stretch"),
    ]},
    "Pacing & flow": {"weight": 0.10, "items": [
        Item("speech vs dead air", lambda f: ramp(_a(f, "speech_ratio"), 0.35, 0.70), 0.5, "share of the recording with speech"),
        Item("long pauses (>8 s) per hour", lambda f: ramp(_pauses_per_hour(f), 40, 5), 0.3, "dead-air episodes inside the session"),
        Item("talk balance", lambda f: band(_t(f, "teacher_talk_share"), 0.9, 0.40, 0.65, 0.95), 0.2, "teacher share of talk time"),
    ]},
    "Presentation": {"weight": 0.15, "items": [
        Item("something useful on screen", _visual_content, 0.40, "face or shared content is visible, not black/empty"),
        Item("camera on", lambda f: ramp(_v(f, "black_ratio"), 0.25, 0.0), 0.30, "camera not switched off"),
        Item("face well lit", lambda f: None if _v(f, "dim_face_ratio") is None else ramp(_v(f, "dim_face_ratio"), 0.8, 0.2), 0.30, "face region is bright enough"),
    ]},
}

# Cut-offs on the 0..100 overall score; (Poor|Average, Average|Good, Good|Excellent). Replaced by calibrated values in calibration.json.
DEFAULT_CUTS = (40.0, 52.0, 64.0)


@dataclass
class Score:
    overall: float
    label: str
    confidence: float
    dimensions: dict[str, float | None]
    items: dict[str, list[dict]] = field(default_factory=dict)
    coverage: float = 1.0


def score_dimension(f: dict, dim: str) -> tuple[float | None, list[dict]]:
    items, num, den = [], 0.0, 0.0
    for it in DIMENSIONS[dim]["items"]:
        s = it.get(f)
        items.append({"item": it.name, "score": s, "weight": it.weight, "why": it.why})
        if s is not None:
            num += s * it.weight
            den += it.weight
    total = sum(it.weight for it in DIMENSIONS[dim]["items"])
    # under half the evidence available -> do not pretend the dimension was measured
    return (100 * num / den if den >= 0.5 * total else None), items


def label_for(overall: float, cuts: tuple[float, float, float] = DEFAULT_CUTS) -> str:
    return LABELS[sum(overall >= c for c in cuts)]


def score(f: dict, cuts: tuple[float, float, float] = DEFAULT_CUTS, exclude: set[str] | None = None) -> Score:
    """`exclude` removes dimensions (e.g. Presentation when the platform, not the teacher, caused the fault)."""
    dims, items = {}, {}
    num = den = 0.0
    for d, spec in DIMENSIONS.items():
        s, it = score_dimension(f, d)
        dims[d], items[d] = s, it
        if s is not None and d not in (exclude or set()):
            num += s * spec["weight"]
            den += spec["weight"]
    total_w = sum(v["weight"] for k, v in DIMENSIONS.items() if k not in (exclude or set()))
    coverage = den / total_w if total_w else 0.0
    overall = num / den if den else 0.0
    label = label_for(overall, cuts)
    # confidence: distance to the nearest cut-off (in points) and how much of the rubric had data
    margin = min(abs(overall - c) for c in cuts)
    confidence = round(min(0.95, 0.35 + margin / 12.0) * (0.5 + 0.5 * coverage), 2)
    if coverage < 0.5:  # most of the rubric had no data: never present this as a confident verdict
        confidence = min(confidence, 0.25)
    return Score(round(overall, 1), label, confidence, {k: (None if v is None else round(v, 1)) for k, v in dims.items()}, items, coverage)
