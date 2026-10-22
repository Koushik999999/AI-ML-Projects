"""Measure the no-VTT path on a full recording against its platform VTT (local only; prints aggregates, no text).

python scripts/asr_eval.py KEY [model]   e.g. excellent_b491_B tiny
Reports: realtime factor, word-overlap F1 vs the VTT, speaker-split accuracy on Whisper segments, and the verdict with
and without the VTT.
"""
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import load_recordings  # noqa: E402
from src.assess import assess  # noqa: E402
from src.features.asr import transcribe_audio  # noqa: E402
from src.features.audio import decode_mono  # noqa: E402
from src.features.speakers import assign_speakers  # noqa: E402
from src.features.transcript import pick_teacher  # noqa: E402
from src.pipeline import analyze  # noqa: E402
from src.vtt import load_vtt  # noqa: E402

key, model = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "tiny")
rec = next(r for r in load_recordings() if r.key == key)
truth = load_vtt(rec.vtt)
T = pick_teacher(truth)
audio = decode_mono(rec.video)
t0 = time.time()
res = transcribe_audio(audio, model, progress=lambda f, m: None)
el = time.time() - t0
dur = len(audio) / 16000
print(f"{key} [{model}] audio {dur / 60:.1f} min transcribed in {el / 60:.1f} min -> realtime factor {el / dur:.2f}x, language={res.language}, complete={res.complete}")


def bag(cues):
    return [w for c in cues for w in re.findall(r"[a-z']+", c.text.lower())]


a, b = bag(res.cues), bag(truth)
from collections import Counter  # noqa: E402
ca, cb = Counter(a), Counter(b)
ov = sum((ca & cb).values())
p, r_ = ov / max(len(a), 1), ov / max(len(b), 1)
print(f"words: whisper {len(a)} vs platform {len(b)}; bag-of-words F1 = {2 * p * r_ / max(p + r_, 1e-9):.2f}")

lab, info = assign_speakers(audio, res.cues)
ok = tot = 0.0
for c in lab:
    ov_by = Counter()
    for tc in truth:
        o = min(c.end, tc.end) - max(c.start, tc.start)
        if o > 0:
            ov_by[tc.speaker == T] += o
    if ov_by:
        w = c.end - c.start
        tot += w
        ok += w * ((ov_by.most_common(1)[0][0]) == (c.speaker == "Teacher"))
base = sum((c.end - c.start) for c in lab)
print(f"speaker split on Whisper segments: time-weighted agreement with VTT labels = {ok / max(tot, 1e-9):.2f} (separation {info['separation']:.2f})")

with_vtt = assess(analyze(rec.video, rec.vtt, use_cache=True, whisper_model="skip"))
no_vtt = assess(analyze(rec.video, None, use_cache=False, whisper_model=model, deadline_s=900))
for name, r in (("with VTT", with_vtt), ("no VTT  ", no_vtt)):
    s = r["score"]
    print(f"{name}: {s['label']:9s} score={s['overall']:5.1f} confidence={s['confidence']:.2f} coverage={s['coverage']:.2f} dims={ {k[:6]: v for k, v in s['dimensions'].items()} }")
