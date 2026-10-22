"""Print the assessment for a cached recording (batch-code keys only)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assess import assess
from src.scoring.technical import fmt_t
for key in sys.argv[1:]:
    d = json.loads(Path(f"cache/rec_{key}.json").read_text()); r = assess(d["features"]); s = r["score"]
    print(f"\n##### {key}  (true: {d['rec']['label'] or d['rec']['folder']})  ->  {s['label']}  score={s['overall']}  conf={s['confidence']}")
    print("dims:", {k: v for k, v in s["dimensions"].items()})
    for o in r["observations"]:
        print(f" [{o['polarity'][:3]}] {o['dimension']}: {o['text']}" + (f"\n        -> {o['suggestion']}" if o.get("suggestion") else ""))
    for p in r["technical"]["platform"]: print(" [PLATFORM]", p["text"])
    for p in r["technical"]["setup"]: print(" [SETUP]", p["text"])
    for n in r["notes"]: print(" [NOTE]", n)
