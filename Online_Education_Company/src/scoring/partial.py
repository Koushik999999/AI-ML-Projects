"""Detect partial recordings, where opening-only and closing-only checks cannot fairly be assessed.

A clip of the middle of a lesson has no greeting, recap, goodbye or homework simply because those moments are not in it.
Penalising (or praising) their absence would be a measurement error, so such checks are marked "not assessable" and left out of the
score; per-minute rate signals (praise rate, talk balance, silences, child turns) are kept.

Thresholds are generic round numbers, not fitted to the sample classes (all labelled classes run 38-89 min and start speaking
between 0:21 and 4:08).
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_FULL_CLASS_S = 20 * 60   # shorter than this: a clip, not a whole class
LATE_START_S = 10 * 60       # first speech later than this: the opening is not in the recording

OPENING_CHECKS = ("rapport check-in", "greeting", "new-joiner introduction")
CLOSING_CHECKS = ("homework", "recap", "closing")


@dataclass(frozen=True)
class Partial:
    is_partial: bool = False
    skip_opening: bool = False
    skip_closing: bool = False
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def not_assessable(self) -> list[str]:
        return (list(OPENING_CHECKS) if self.skip_opening else []) + (list(CLOSING_CHECKS) if self.skip_closing else [])

    @property
    def reliability(self) -> float:
        """Multiplier for confidence: fewer checks were possible, so the verdict is less certain."""
        return 0.8 if self.skip_opening else (0.9 if self.skip_closing else 1.0)


def partial_info(features: dict) -> Partial:
    media = features.get("media") or {}
    t = features.get("transcript") or {}
    dur = media.get("duration_s") or 0.0
    reasons: list[str] = []
    skip_open = skip_close = False
    if 0 < dur < MIN_FULL_CLASS_S:
        reasons.append(f"the recording is only {dur / 60:.0f} min long")
        skip_open = skip_close = True
    if t.get("ok") and t.get("session_start_s", 0.0) > LATE_START_S:
        reasons.append(f"the first speech is at {t['session_start_s'] / 60:.0f} min, so the start of the class is not included")
        skip_open = skip_close = True
    asr = t.get("asr") or {}
    cut = bool(media.get("truncated")) or (asr.get("total_s") is not None and asr.get("covered_s", 0) < asr["total_s"] - 1.0)
    if cut:
        reasons.append("only the first part of the recording was analysed, so the end of the class is not included")
        skip_close = True
    return Partial(bool(reasons), skip_open, skip_close, tuple(reasons))
