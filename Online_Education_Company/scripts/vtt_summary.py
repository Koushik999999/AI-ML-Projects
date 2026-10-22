"""Print per-transcript stats (speakers, words, language mix). Names are NOT printed: speakers shown as S1, S2..."""
import re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vtt import load_vtt

root = Path("data/class recordings")
for p in sorted(root.glob("*/*.vtt")):
    cues = load_vtt(p)
    words = Counter(); 
    for c in cues: words[c.speaker or "?"] += c.words
    order = [s for s, _ in words.most_common()]
    alias = {s: f"S{i+1}" for i, s in enumerate(order)}
    txt = " ".join(c.text for c in cues)
    mal = len(re.findall(r"[\u0d00-\u0d7f]", txt)); 
    tot = sum(words.values())
    dur = cues[-1].end if cues else 0
    print(f"{p.parent.name:14s}{p.name[:22]:24s} cues={len(cues):4d} words={tot:5d} first={cues[0].start:6.0f}s last={dur:6.0f}s "
          f"speakers={len(words)} top={[(alias[s], w) for s, w in words.most_common(4)]} malayalam_chars={mal}")
