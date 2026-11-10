"""Blur license plates in one image or in every image of a folder."""

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
    ap.add_argument("--input", required=True, help="image file or folder of images")
    ap.add_argument("--output", required=True, help="output file (for one image) or folder (for a folder)")
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF)
    ap.add_argument("--pad", type=float, default=DEFAULT_PAD)
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    args = ap.parse_args()

    import cv2

    from lpblur.blur import anonymize, load_model

    src, dst = Path(args.input), Path(args.output)
    if src.is_dir():
        pairs = [(p, dst / p.name) for p in sorted(src.iterdir()) if p.suffix.lower() in IMAGE_EXTS]
    elif src.is_file():
        pairs = [(src, dst / src.name if dst.is_dir() else dst)]
    else:
        sys.exit(f"input not found: {src}")
    if not pairs:
        sys.exit(f"no images found in {src}")

    model = load_model(args.weights)
    for s, d in pairs:
        d.parent.mkdir(parents=True, exist_ok=True)
        _, blurred, boxes = anonymize(str(s), model, args.conf, args.pad, args.imgsz)
        cv2.imwrite(str(d), blurred)
        print(f"{s.name}: {len(boxes)} plate(s) blurred -> {d}")


if __name__ == "__main__":
    main()
