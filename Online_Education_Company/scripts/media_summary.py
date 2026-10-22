import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.media import probe, ffmpeg_exe
print("ffmpeg:", ffmpeg_exe())
for p in sorted(Path("data/class recordings").glob("*/*.mp4")):
    m = probe(p)
    print(f"{p.parent.name:14s}{p.name[:20]:22s} dur={m.duration/60:5.1f}m {m.width}x{m.height} fps={m.fps} ch={m.audio_channels} sr={m.sample_rate} size={p.stat().st_size/1e6:6.0f}MB")
