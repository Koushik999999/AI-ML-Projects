import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vtt import load_vtt
p, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
cues = load_vtt(p); w = Counter()
for c in cues: w[c.speaker] += c.words
al = {s: f"S{i+1}" for i, (s, _) in enumerate(w.most_common())}
for c in cues:
    if a <= c.start <= b: print(f"[{int(c.start//60):02d}:{int(c.start%60):02d}] {al[c.speaker]}: {c.text[:150]}")
