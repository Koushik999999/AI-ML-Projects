"""End-to-end smoke test of the app code path on a short clip: python scripts/e2e_smoke.py CLIP.mp4 [TRANSCRIPT.vtt]"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assess import assess  # noqa: E402
from src.pipeline import analyze  # noqa: E402

clip, vtt = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
for name, v in [("with VTT", vtt), ("no VTT, ASR skipped", None)]:
    t = time.time()
    steps = []
    f = analyze(clip, v, use_cache=False, whisper_model="skip", max_minutes=3, progress=lambda p, m: steps.append(m))
    r = assess(f)
    print(f"[{name}] {time.time() - t:.1f}s label={r['score']['label']} overall={r['score']['overall']} "
          f"conf={r['score']['confidence']} coverage={r['score']['coverage']:.2f} progress_steps={len(steps)}")
    print("   notes:", [n[:100] for n in r["notes"]])
    print("   dims:", r["score"]["dimensions"], "| n_obs:", len(r["observations"]))
for bad in ["definitely_missing.mp4"]:
    try:
        analyze(bad, None, use_cache=False)
    except Exception as e:  # noqa: BLE001
        print("bad input ->", type(e).__name__, str(e)[:90])
