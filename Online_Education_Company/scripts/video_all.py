import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.features.video import video_features  # noqa: E402

out = Path("cache"); out.mkdir(exist_ok=True)
for mp4 in sorted(Path("data/class recordings").glob("*/*.mp4")):
    b = (re.search(r"B\d{3}", mp4.name) or re.search(r"(english|malayalam)", mp4.name, re.I))[0].lower()
    lvl = "I" if "intermediate" in mp4.name.lower() else "B"
    key = f"{mp4.parent.name.replace(' ', '')}_{b}{lvl}"
    t = time.time(); f = video_features(mp4)
    (out / f"video_{key}.json").write_text(json.dumps(f))
    print(f"{key:24s} black={f['black_ratio']:.2f} face={f['face_ratio']:.2f} multi={f['multi_face_ratio']:.2f} screen={f['screen_ratio']:.2f} "
          f"change={f['change_rate']:.2f} faceH={f['median_face_height_frac']:.2f} faceLum={f['face_brightness']} dim={f['dim_face_ratio']} "
          f"static={len(f['static_runs'])} frozen={len(f['frozen_runs'])} camoff={len(f['camera_off_runs'])} ({time.time()-t:.0f}s)", flush=True)
