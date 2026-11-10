"""Blur license plates in a video file, frame by frame."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True, help="trained weights, e.g. weights/best.pt")
    ap.add_argument("--input", required=True, help="input video file")
    ap.add_argument("--output", required=True, help="output .mp4 path")
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF)
    ap.add_argument("--pad", type=float, default=DEFAULT_PAD)
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    args = ap.parse_args()

    from lpblur.blur import load_model
    from lpblur.video import blur_video

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    n, fps = blur_video(args.input, args.output, load_model(args.weights), args.conf, args.pad, args.imgsz)
    print(f"processed {n} frames at {fps:.0f} FPS (read + detect + blur + write) -> {args.output}")


if __name__ == "__main__":
    main()
