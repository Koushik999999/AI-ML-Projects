import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.features.audio import decode_mono, audio_features
for mp4 in sorted(Path("data/class recordings").glob("*/*.mp4")):
    t = time.time(); f = audio_features(decode_mono(mp4)); f.pop("speech_mask_100ms", None); f.pop("activity_10s", None)
    print(f"{mp4.parent.name[:7]:8s}{mp4.name[:10]:11s} speech={f['speech_ratio']:.2f} longPauses={len(f['long_pauses'])} longest={f['longest_pause_s']:.0f}s floor={f['noise_floor_db']:.0f}dB med={f['median_speech_db']:.0f}dB snr={f['snr_db']:.0f} clip={f['clipping_ratio']*100:.2f}% digSil={f['digital_silence_ratio']:.2f} dropouts={len(f['dropouts'])} ({time.time()-t:.0f}s)", flush=True)
