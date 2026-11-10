"""Evaluate a trained plate detector: metrics, recall vs confidence, recall by plate size, optional OCR check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True, help="trained weights, e.g. runs/lp_v8s/weights/best.pt")
    ap.add_argument("--root", default="data", help="dataset root with images/<split>, labels/<split> and data.yaml")
    ap.add_argument("--split", default="val", choices=["train", "val", "test"])
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF, help="operating threshold for the size table / OCR")
    ap.add_argument("--pad", type=float, default=DEFAULT_PAD, help="box padding used by the OCR check")
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--skip-curve", action="store_true", help="skip recall-vs-confidence and recall-by-size")
    ap.add_argument("--ocr", action="store_true", help="also run the EasyOCR leak check (needs easyocr)")
    args = ap.parse_args()

    from lpblur.blur import load_model
    from lpblur.evaluate import gt_hits, recall_by_size, recall_vs_conf, val_metrics

    model = load_model(args.weights)
    data_yaml = f"{args.root}/data.yaml"

    print(f"== Ultralytics metrics ({args.split}) ==")
    print({k: round(float(v), 3) for k, v in val_metrics(model, data_yaml, args.split, args.imgsz, args.batch).items()})

    if not args.skip_curve:
        print("\n== Recall vs confidence ==")
        print(recall_vs_conf(model, args.root, args.split, imgsz=args.imgsz).to_string(index=False))
        print(f"\n== Recall by plate width (conf = {args.conf}) ==")
        print(recall_by_size(gt_hits(model, args.root, args.split, args.conf, imgsz=args.imgsz)).to_string())

    if args.ocr:
        import torch

        from lpblur.ocr_check import make_reader, ocr_leak_check

        res = ocr_leak_check(model, make_reader(torch.cuda.is_available()), args.root, args.split,
                             args.conf, args.pad, args.imgsz)
        print("\n== OCR leak check ==")
        print(f"plates: {res['plates']} | readable before: {res['readable_before']} | "
              f"readable after: {res['readable_after']} | leak rate: {res['leak_rate']:.1%}")


if __name__ == "__main__":
    main()
