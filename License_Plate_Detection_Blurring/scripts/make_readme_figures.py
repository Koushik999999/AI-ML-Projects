"""Regenerate the README before/after figures from a folder of sample images (plates hidden on the left)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True, help="trained weights, e.g. weights/best.pt")
    ap.add_argument("--images", required=True, help="folder of sample images you are allowed to publish")
    ap.add_argument("--output", default="docs/assets/before_after.png", help="output figure path")
    ap.add_argument("--title", default="Plates in examples are hidden")
    ap.add_argument("--n", type=int, default=3, help="number of images (first n by file name)")
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF)
    ap.add_argument("--pad", type=float, default=DEFAULT_PAD)
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    args = ap.parse_args()

    if not Path(args.weights).is_file():
        sys.exit(f"weights not found: {args.weights} (see the Dataset section of the README for the download link)")
    folder = Path(args.images)
    paths = sorted(str(p) for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)[: args.n] if folder.is_dir() else []
    if not paths:
        sys.exit(f"no images found in: {args.images}")

    from lpblur.blur import load_model
    from lpblur.viz import before_after

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    before_after(paths, load_model(args.weights), args.title, args.conf, args.pad, args.imgsz,
                 save_path=args.output, hide_original=True)
    print(f"saved {args.output}")


if __name__ == "__main__":
    main()
