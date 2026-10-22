"""Evaluate the label-free teacher/student heuristic on real audio, using VTT labels as ground truth (local only)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import load_recordings  # noqa: E402
from src.features.audio import decode_mono  # noqa: E402
from src.features.speakers import validate_against_labels  # noqa: E402
from src.features.transcript import pick_teacher  # noqa: E402
from src.vtt import load_vtt  # noqa: E402

print("recording".ljust(26), "true_student_share  heuristic_acc  baseline(all-teacher)  stu_precision  stu_recall  separation")
res = []
for r in load_recordings():
    cues = load_vtt(r.vtt)
    v = validate_against_labels(decode_mono(r.video), cues, pick_teacher(cues))
    res.append(v)
    print(r.key.ljust(26), f"{v['student_share_true']:.2f}".ljust(19), f"{v['time_weighted_accuracy']:.2f}".ljust(13), f"{v['baseline_all_teacher']:.2f}".ljust(22),
          f"{v['student_precision']:.2f}".ljust(14), f"{v['student_recall']:.2f}".ljust(11), f"{v['separation']:.2f}", flush=True)
n = len(res)
print(f"MEAN accuracy {sum(v['time_weighted_accuracy'] for v in res) / n:.2f} vs baseline {sum(v['baseline_all_teacher'] for v in res) / n:.2f}")
