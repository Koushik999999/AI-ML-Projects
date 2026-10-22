"""Step-1 summary table: media + transcript stats per recording (batch codes only, no names)."""
import re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vtt import load_vtt
from src.media import probe
MANGLISH = set("aanu illa enthu entha cheyyu cheyyan ningal njan ente ithu athu alle ayyo sheri shari mone mole chechi chetta kutty paranju nokku nokkam vaa poyi undu undo ariyam ariyilla venam venda".split())
rows = []
root = Path("data/class recordings")
for mp4 in sorted(root.glob("*/*.mp4")):
    label = mp4.parent.name
    vtt = [v for v in mp4.parent.glob("*.vtt")
           if (re.search(r"B\d{3}", mp4.name) and re.search(r"B\d{3}", v.name) and re.search(r"B\d{3}", mp4.name)[0] == re.search(r"B\d{3}", v.name)[0]
               and (mp4.parent.name != "good" or ("intermediate" in mp4.name.lower()) == ("intermediate" in v.name.lower())))
           or (label == "demo" and mp4.stem.lower().split()[-1] in v.name.lower())]
    m = probe(mp4); cues = load_vtt(vtt[0]) if vtt else []
    w = Counter()
    for c in cues: w[c.speaker] += c.words
    toks = [t for c in cues for t in re.findall(r"[a-z']+", c.text.lower())]
    mg = sum(t in MANGLISH for t in toks) / max(len(toks), 1)
    lvl = "Intermediate" if "intermediate" in mp4.name.lower() else "Beginner" if "beginner" in mp4.name.lower() else "-"
    rows.append((label, re.search(r"B\d{3}", mp4.name)[0] if re.search(r"B\d{3}", mp4.name) else mp4.stem.split()[-1], lvl, m, sum(w.values()), len(w), mg, bool(vtt)))
print("| label | batch | level | duration | res | fps | audio | words | speakers | manglish tokens | vtt |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for l, b, lv, m, wc, sp, mg, hv in rows:
    print(f"| {l} | {b} | {lv} | {m.duration/60:.1f} min | {m.width}x{m.height} | {m.fps:.0f} | {m.audio_channels}ch {m.sample_rate} | {wc} | {sp} | {mg*100:.1f}% | {'y' if hv else 'N'} |")
