"""No-VTT end-to-end check on a short clip: python scripts/e2e_no_vtt.py CLIP.mp4 [real|fake]

real: asks for the real faster-whisper model (needs the model download; on an offline machine this MUST fall back).
fake: injects a stand-in ASR model that returns canned segments, to exercise chunking + speaker assignment + scoring
      on real audio. It says nothing about recognition quality.
"""
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assess import assess  # noqa: E402
from src.pipeline import analyze  # noqa: E402

clip, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "real")


class Fake:
    """~1 short segment every 6 s, alternating text so the pipeline has something to work with."""
    texts = ["Hello how are you today?", "I am fine", "Today we learn the knight. Understood?", "Yes", "Very good, great job!", "Okay next one"]

    def transcribe(self, audio, **kw):
        n = int(len(audio) / 16000 // 6)
        segs = [SimpleNamespace(start=i * 6.0, end=i * 6.0 + 2.5, text=self.texts[i % 6]) for i in range(n)]
        return segs, SimpleNamespace(language="en")


steps = []
t = time.time()
f = analyze(clip, None, use_cache=False, whisper_model="tiny", max_minutes=3, deadline_s=300,
            asr_model=Fake() if mode == "fake" else None, progress=lambda p, m: steps.append(m))
r = assess(f)
print(f"[{mode}] {time.time() - t:.1f}s  label={r['score']['label']} overall={r['score']['overall']} confidence={r['score']['confidence']} coverage={r['score']['coverage']:.2f}")
print("  transcript source:", f["transcript"].get("source"), "| approximate speakers:", f["transcript"].get("speakers_approximate"),
      "| asr:", {k: v for k, v in (f["transcript"].get("asr") or {}).items() if k != "speaker_separation"})
print("  UNAVAILABLE:", [(u["signal"], u["reason"]) for u in r["unavailable"]])
print("  dims:", r["score"]["dimensions"])
print("  notes:", [n[:110] for n in r["notes"]])
print("  progress messages:", sorted(set(s[:45] for s in steps)))
