"""Audit a YOLO-format dataset; optionally clean it and write data.yaml."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur.dataset import (  # noqa: E402
    SPLITS, audit_dataset, clean_dataset, find_leakage, source_bases, write_data_yaml,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="data", help="dataset root with images/<split> and labels/<split>")
    ap.add_argument("--clean", action="store_true",
                    help="move images with missing/empty labels and leaked val images to --removed, then write data.yaml")
    ap.add_argument("--removed", default="data_removed", help="where --clean moves files (nothing is deleted)")
    args = ap.parse_args()

    df, problems, cols = audit_dataset(args.root)
    imgs = df.drop_duplicates(["split", "img"])
    print(f"labelled images: {len(imgs)} | plates: {len(df)} | columns per label line: {dict(cols)}")
    print("problems:", dict(Counter((s, r) for s, _, r in problems)))
    print("plate size (px) / area (%):\n", df[["w_px", "h_px", "area_pct", "aspect"]].describe().round(2).to_string())
    print("source photos shared between splits:", {k: len(v) for k, v in find_leakage(source_bases(df)).items()})

    if args.clean:
        print("moved:", clean_dataset(args.root, args.removed))
        print("wrote", write_data_yaml(args.root))
        print("splits:", {s: len(list(Path(args.root, "images", s).iterdir())) for s in SPLITS})


if __name__ == "__main__":
    main()
