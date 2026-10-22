"""Numeric-only layout probe (no image is ever displayed or exported)."""
import sys, subprocess
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.media import ffmpeg_exe
W, H = 640, 360
def frames(path, at, n=3, step=20):
    out = []
    for k in range(n):
        t = at + k * step
        r = subprocess.run([ffmpeg_exe(), "-loglevel", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
        if len(r.stdout) == W*H*3: out.append(np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3))
    return out
cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
for p in sys.argv[1:]:
    print("==", Path(p).parent.name, Path(p).name[:14])
    for f in frames(p, 600):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        grid = g.reshape(4, H//4, 8, W//8).mean(axis=(1, 3)).astype(int)   # 4 rows x 8 cols luma
        faces = cas.detectMultiScale(g, 1.1, 5, minSize=(24, 24))
        dark = (g < 20).mean()
        print(" luma grid:", grid.tolist(), "dark%%=%.2f" % dark, "faces:", [tuple(int(v) for v in b) for b in faces][:6])
