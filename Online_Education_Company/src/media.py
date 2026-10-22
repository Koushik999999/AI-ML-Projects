"""ffmpeg helpers. Uses the system ffmpeg if present, else the binary bundled by imageio-ffmpeg."""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


def ffmpeg_exe() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


@dataclass(frozen=True)
class MediaInfo:
    duration: float
    width: int | None
    height: int | None
    fps: float | None
    audio_channels: int | None
    sample_rate: int | None
    has_video: bool
    has_audio: bool


def probe(path: str | Path) -> MediaInfo:
    """Parse `ffmpeg -i` stderr (ffprobe is not always available)."""
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace")
    err = r.stderr
    d = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    dur = int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]) if d else 0.0
    v = re.search(r"Stream #\S+.*?Video:.*?,\s*(\d{2,5})x(\d{2,5})", err)
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", err)
    a = re.search(r"Stream #\S+.*?Audio:.*?,\s*(\d+)\s*Hz,\s*(mono|stereo|\d+ channels|[\d.]+)", err)
    ch = {"mono": 1, "stereo": 2}.get(a[2]) if a else None
    if a and ch is None:
        m = re.match(r"(\d+)", a[2]); ch = int(m[1]) if m else None
    return MediaInfo(dur, int(v[1]) if v else None, int(v[2]) if v else None,
                     float(fps[1]) if fps else None, ch, int(a[1]) if a else None, bool(v), bool(a))


def extract_audio(path: str | Path, out_wav: str | Path, sr: int = 16000) -> Path:
    """Mono 16 kHz WAV for local analysis (never leaves the machine)."""
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr),
                    str(out_wav)], check=True)
    return Path(out_wav)
