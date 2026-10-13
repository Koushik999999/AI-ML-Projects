"""Copy saved runs into results/judge_variance/rep<k>/<label>/ so the existing `--judge-only` path can
re-judge them. Originals are never modified. Each copy is marked judge_pending, and its `sample` is set to
1000*k + original so the judge's response-cache key differs per repeat (otherwise repeat k would just replay
the cached verdict). Judge-only never calls the agent or the simulator.

    python scripts/prepare_judge_variance.py          # then: python scripts/prepare_judge_variance.py --list
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "judge_variance"
REPS = 3
SOURCES = {  # label -> (results dir, scenario)
    "v1_reschedule_happy": ("baseline_v1", "reschedule_happy"),
    "v2_reschedule_happy": ("candidate_v2", "reschedule_happy"),
    "v1_reschedule_race": ("baseline_v1_heldout", "reschedule_race"),
    "v2_reschedule_race": ("candidate_v2_heldout", "reschedule_race"),
    "v1_book_happy": ("baseline_v1", "book_happy"),
    "v2_book_happy": ("candidate_v2", "book_happy"),
}


def dirs():
    return [OUT / f"rep{k}" / label for k in range(1, REPS + 1) for label in SOURCES]


def prepare():
    for k in range(1, REPS + 1):
        for label, (src, scenario) in SOURCES.items():
            dst = OUT / f"rep{k}" / label
            (dst / "runs").mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / "results" / src / "meta.json", dst / "meta.json")
            for f in sorted((ROOT / "results" / src / "runs").glob(f"{scenario}__s*.json")):
                rec = json.loads(f.read_text(encoding="utf-8"))
                orig = rec["sample"]
                rec.update({"sample": 1000 * k + orig, "orig_sample": orig, "source_dir": src,
                            "judge": None, "judge_pending": True, "passed": None})
                (dst / "runs" / f"{scenario}__s{rec['sample']}.json").write_text(
                    json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("\n".join(str(d) for d in dirs()))
    else:
        prepare()
        print(f"prepared {len(dirs())} directories under {OUT}")
