"""Recompute only the transcript section of cached features (fast) after changing transcript.py."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import load_recordings  # noqa: E402
from src.features.transcript import transcript_features  # noqa: E402
from src.vtt import load_vtt  # noqa: E402

for r in load_recordings():
    p = Path("cache") / f"rec_{r.key}.json"
    d = json.loads(p.read_text())
    dur = d["features"]["media"]["duration_s"]
    d["features"]["transcript"] = {**transcript_features(load_vtt(r.vtt), dur), "source": "vtt"}
    p.write_text(json.dumps(d, default=float))
print("refreshed")
