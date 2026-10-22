"""Compare a name-free teacher heuristic with ground truth from feedbacks.pdf. Prints only OK/MISS, never names."""
import re, sys
from collections import Counter
from pathlib import Path
import pypdf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vtt import load_vtt
root = Path("data/class recordings")
txt = "\n".join(p.extract_text() for p in pypdf.PdfReader(root / "feedbacks.pdf").pages)
truth = {}   # batch code -> name tokens
for m in re.finditer(r"(B\d{3})\s*\(([^)]*)\)\s*([A-Za-z ]+?)\s*-{3,}", txt):
    truth[m[1]] = set(m[3].lower().split())
HONOR = re.compile(r"\b(sir|ma'?am|madam|miss|teacher)\b", re.I)
for p in sorted(root.glob("*/*.vtt")):
    code = re.search(r"B\d{3}", p.name); code = code[0] if code else None
    cues = load_vtt(p); w = Counter(); hon = Counter()
    for i, c in enumerate(cues):
        w[c.speaker] += c.words
        if HONOR.search(c.text) and i + 1 < len(cues):  # someone says "sir" -> likely addressing teacher; credit the nearby *other* speakers
            for d in (-2, -1, 1, 2):
                j = i + d
                if 0 <= j < len(cues) and cues[j].speaker != c.speaker: hon[cues[j].speaker] += 1
    by_words = w.most_common(1)[0][0]
    tkey = truth.get(code)
    if not tkey: print(p.parent.name, p.name[:12], "no ground truth"); continue
    gt = [s for s in w if s and set(s.lower().split()) & tkey]
    print(f"{p.parent.name:14s}{p.name[:12]:14s} truth_found={bool(gt)} top_words_is_teacher={by_words in gt} rank_of_teacher_by_words={[s for s,_ in w.most_common()].index(gt[0])+1 if gt else '-'}")
