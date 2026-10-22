"""WebVTT parsing for speaker-labelled meeting transcripts ("Name: text")."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")
_SPK = re.compile(r"^([^:\n]{1,60}?):\s+(.*)$", re.S)


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    speaker: str | None
    text: str

    @property
    def words(self) -> int:
        return len(self.text.split())


def _sec(h: str | None, m: str, s: str, ms: str) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(text: str) -> list[Cue]:
    """Parse VTT text into cues. Speaker is None when no 'Name:' prefix is present."""
    cues: list[Cue] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        for i, ln in enumerate(lines):
            m = _TS.search(ln)
            if not m:
                continue
            g = m.groups()
            body = " ".join(lines[i + 1:]).strip()
            if not body:
                break
            sm = _SPK.match(body)
            speaker, content = (sm.group(1).strip(), sm.group(2).strip()) if sm else (None, body)
            cues.append(Cue(_sec(*g[:4]), _sec(*g[4:]), speaker, content))
            break
    return cues


def load_vtt(path: str | Path) -> list[Cue]:
    return parse_vtt(Path(path).read_text(encoding="utf-8-sig", errors="replace"))
