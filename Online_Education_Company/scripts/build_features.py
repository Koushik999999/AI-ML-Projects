"""Compute + cache features for every local recording via the same pipeline the app uses."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import load_recordings  # noqa: E402
from src.pipeline import analyze  # noqa: E402

Path("cache").mkdir(exist_ok=True)
index = {}
for r in load_recordings():
    t = time.time()
    f = analyze(r.video, r.vtt, whisper_model="skip", progress=lambda p, m: None)
    out = Path("cache") / f"rec_{r.key}.json"
    out.write_text(json.dumps({"rec": {"key": r.key, "folder": r.folder, "label": r.label, "level": r.level}, "features": f}, default=float))
    index[r.key] = str(out)
    v = f["video"]
    print(f"{r.key:26s} {time.time()-t:4.0f}s  face={v.get('face_ratio', 0):.2f} screen={v.get('screen_ratio', 0):.2f} black={v.get('black_ratio', 0):.2f} "
          f"warnings={len(f['warnings'])}", flush=True)
