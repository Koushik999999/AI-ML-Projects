"""Locate the labelled dataset (local only) and pair each recording with its transcript."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path("data/class recordings")
LABELS = {"weak": "Poor", "average": "Average", "good": "Good", "excellent": "Excellent"}


@dataclass(frozen=True)
class Rec:
    key: str
    folder: str
    label: str | None      # Poor/Average/Good/Excellent, None for quality/demo
    level: str             # Beginner/Intermediate/Unknown
    video: Path
    vtt: Path | None


def load_recordings() -> list[Rec]:
    recs: list[Rec] = []
    for mp4 in sorted(ROOT.glob("*/*.mp4")):
        folder = mp4.parent.name
        m = re.search(r"B\d{3}", mp4.name)
        code = m[0].lower() if m else mp4.stem.split()[-1].lower()
        level = "Intermediate" if "intermediate" in mp4.name.lower() else "Beginner" if "beginner" in mp4.name.lower() else "Unknown"
        vtts = list(mp4.parent.glob("*.vtt"))
        if m:
            vtts = [v for v in vtts if re.search(m[0], v.name)]
            if len(vtts) > 1:  # two classes of the same batch in one folder (not the case today, but be safe)
                vtts = [v for v in vtts if ("intermediate" in v.name.lower()) == (level == "Intermediate")]
        else:
            vtts = [v for v in vtts if code in v.name.lower()]
        recs.append(Rec(f"{folder.replace(' ', '')}_{code}_{level[0]}", folder, LABELS.get(folder), level, mp4, vtts[0] if vtts else None))
    return recs
