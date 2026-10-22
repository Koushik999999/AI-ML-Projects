import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.features.transcript import transcript_features  # noqa: E402
from src.vtt import load_vtt  # noqa: E402

cols = ["teacher_talk_share", "student_turns_per_min", "n_students_spoke", "n_students_asked_individually",
        "questions_per_min", "open_question_share", "median_response_latency_s", "longest_monologue_s",
        "overlaps_per_min", "praise_per_10min", "check_per_10min", "energy_marks_per_min", "session_start_s"]
flags = ["has_greeting", "has_rapport", "has_new_joiner_intro", "has_homework", "has_recap", "has_closing",
         "has_prev_class_revision"]
print("label/batch".ljust(18), *[c[:9].ljust(9) for c in cols], "flags(grt,rap,int,hw,rcp,cls,prev)")
for p in sorted(Path("data/class recordings").glob("*/*.vtt")):
    f = transcript_features(load_vtt(p))
    b = (re.search(r"B\d{3}", p.name) or re.search(r"(english|malayalam)", p.name))[0]
    print(f"{p.parent.name[:7]}/{b}".ljust(18),
          *[(f"{f[c]:.2f}" if isinstance(f[c], float) else str(f[c])).ljust(9) for c in cols],
          "".join("Y" if f[k] else "-" for k in flags))
