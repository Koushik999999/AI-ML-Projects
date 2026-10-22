"""Features -> final assessment (label, dimensions, observations, technical flags). Pure functions, no I/O."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.scoring.explain import Observation, observations, pick
from src.scoring.rubric import DEFAULT_CUTS, score
from src.scoring.technical import technical_report

_CAL = Path(__file__).with_name("scoring") / "calibration.json"


def load_cuts() -> tuple[float, float, float]:
    try:
        c = json.loads(_CAL.read_text())["cuts"]
        return (float(c[0]), float(c[1]), float(c[2]))
    except Exception:  # noqa: BLE001
        return DEFAULT_CUTS


def assess(features: dict) -> dict:
    tech = technical_report(features)
    s = score(features, load_cuts(), exclude={"Presentation"} if tech["exclude_presentation"] else None)
    t = features.get("transcript") or {}
    teacher = t.get("_teacher_label")
    names = [n for n in (t.get("_student_turn_counts") or {})] + ([teacher] if teacher else [])
    obs: list[Observation] = pick(observations(features, names, teacher))
    notes: list[str] = list(features.get("warnings", []))
    if tech["exclude_presentation"]:
        notes.append("Heavy platform faults were detected, so the 'Presentation' dimension was excluded from the score (the teacher is not penalised for them).")
    if t.get("ok") and not t.get("lexicon_reliable", True):
        notes.append("The transcript is mostly non-English or garbled (typical for machine transcripts of Malayalam speech), so wording-based checks "
                     "(rapport, praise, homework, recap, closing) were switched off; talk balance, turn-taking and audio/video signals were still used.")
    if not (t.get("ok") and t.get("has_speakers")):
        notes.append("Interaction dimensions are unavailable without a speaker-labelled transcript; the verdict rests on audio/video signals only and is low-confidence.")
    return {
        "score": {"overall": s.overall, "label": s.label, "confidence": s.confidence, "dimensions": s.dimensions,
                  "items": s.items, "coverage": s.coverage},
        "observations": [asdict(o) for o in obs],
        "technical": tech,
        "notes": notes,
        "features": features,
        "names": names,
        "teacher": teacher,
    }
