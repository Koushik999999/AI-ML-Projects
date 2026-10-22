"""Step-3 analysis on cached features: feature separation by label, rubric scores, honest leave-one-out.

LOO protocol: the rubric ranges are fixed in code (not fitted). The only fitted parameters are the 3 label cut-offs,
set as midpoints between adjacent class means of the overall score on the 7 training recordings, then applied to the
held-out one. With n=8 this is a sanity check, not a performance claim.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assess import load_cuts  # noqa: E402
from src.scoring.rubric import DIMENSIONS, LABELS, label_for, score  # noqa: E402

CUTS = load_cuts()
from src.scoring.technical import technical_report  # noqa: E402

recs = [json.loads(p.read_text()) for p in sorted(Path("cache").glob("rec_*.json"))]
lab = [r for r in recs if r["rec"]["label"]]
others = [r for r in recs if not r["rec"]["label"]]
y = {r["rec"]["key"]: LABELS.index(r["rec"]["label"]) for r in lab}


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) and np.std(rb) else float("nan")


# ---------- 1. raw feature separation ----------
FEATS = [("transcript", k) for k in ["teacher_talk_share", "student_turns_per_min", "n_students_asked_individually", "student_top_share",
                                   "questions_per_min", "open_question_share", "median_response_latency_s", "longest_monologue_s",
                                   "longest_student_silence_s", "first_student_after_s", "praise_per_10min", "check_per_10min",
                                   "energy_marks_per_min", "teacher_words_per_min"]] + \
        [("audio", k) for k in ["speech_ratio", "longest_pause_s", "clipping_ratio", "median_speech_db"]] + \
        [("video", k) for k in ["face_ratio", "screen_ratio", "black_ratio", "change_rate", "dim_face_ratio", "median_face_height_frac"]]
print("\n== raw features: mean by label (P/A/G/E), Spearman vs ordinal label ==")
print("feature".ljust(34), "Poor   Avg    Good   Excel  rho")
for sec, k in FEATS:
    vals = [(r["features"][sec].get(k)) for r in lab]
    if any(v is None for v in vals):
        continue
    by = [np.mean([v for v, r in zip(vals, lab) if y[r["rec"]["key"]] == c]) for c in range(4)]
    rho = spearman(vals, [y[r["rec"]["key"]] for r in lab])
    print(f"{sec[:1]}.{k}".ljust(34), *[f"{b:6.2f}" for b in by], f"{rho:+.2f}")

# ---------- 2. rubric scores ----------
print("\n== rubric scores (shipped cuts %s; set by eye, IN-SAMPLE) ==" % (CUTS,))
dn = list(DIMENSIONS)
print("recording".ljust(28), "true      pred      overall", *[d[:8].ljust(8) for d in dn], "tech(platform/setup)")
overall = {}
for r in lab + others:
    f = r["features"]; tr = technical_report(f)
    s = score(f, CUTS, exclude={"Presentation"} if tr["exclude_presentation"] else None)
    overall[r["rec"]["key"]] = s.overall
    print(r["rec"]["key"].ljust(28), (r["rec"]["label"] or r["rec"]["folder"]).ljust(9), s.label.ljust(9), f"{s.overall:6.1f}  ",
          *[(f"{s.dimensions[d]:.0f}" if s.dimensions[d] is not None else "-").ljust(8) for d in dn], f"{len(tr['platform'])}/{len(tr['setup'])}")

# ---------- 3. leave-one-out ----------
_pred = {k: LABELS.index(label_for(overall[k], CUTS)) for k in y}
print(f"\nIN-SAMPLE with shipped cuts: exact {sum(_pred[k] == y[k] for k in y)}/8, within-one {sum(abs(_pred[k] - y[k]) <= 1 for k in y)}/8 "
      f"(optimistic: cuts were set by eye on these same 8)")
print("\n== leave-one-out on the 8 labelled recordings (out-of-sample estimate) ==")
keys = [r["rec"]["key"] for r in lab]
hits = near = 0
for k in keys:
    train = [q for q in keys if q != k]
    means = [np.mean([overall[q] for q in train if y[q] == c]) for c in range(4)]
    cuts = tuple((means[i] + means[i + 1]) / 2 for i in range(3))
    pred = LABELS.index(label_for(overall[k], cuts))
    hits += pred == y[k]; near += abs(pred - y[k]) <= 1
    print(f"{k:28s} true={LABELS[y[k]]:9s} pred={LABELS[pred]:9s} score={overall[k]:5.1f} cuts={tuple(round(c, 1) for c in cuts)}")
print(f"exact {hits}/8   within-one-class {near}/8   (majority-class baseline exact = 2/8)")
print("Spearman(overall, true label) =", round(spearman([overall[k] for k in keys], [y[k] for k in keys]), 2))
full_means = [np.mean([overall[q] for q in keys if y[q] == c]) for c in range(4)]
print("class means (all 8):", [round(m, 1) for m in full_means], "-> midpoint cuts", tuple(round((full_means[i] + full_means[i + 1]) / 2, 1) for i in range(3)))
