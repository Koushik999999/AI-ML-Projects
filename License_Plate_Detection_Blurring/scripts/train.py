"""Train YOLOv8s on a one-class license plate dataset (same hyperparameters as the notebook)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur import DEFAULT_IMGSZ, DEFAULT_SEED  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/data.yaml", help="YOLO data.yaml (see configs/data.yaml.example)")
    ap.add_argument("--weights", default="yolov8s.pt", help="starting weights (downloaded automatically)")
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--close-mosaic", type=int, default=5, help="epochs at the end without mosaic augmentation")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--project", default="runs", help="output directory for runs")
    ap.add_argument("--name", default="lp_v8s", help="run name (weights land in <project>/<name>/weights/best.pt)")
    ap.add_argument("--device", default=None, help="e.g. 0 for the first GPU, or cpu (default: auto)")
    args = ap.parse_args()

    from ultralytics import YOLO

    YOLO(args.weights).train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, workers=args.workers,
        patience=args.patience, close_mosaic=args.close_mosaic, seed=args.seed,
        project=args.project, name=args.name, exist_ok=True, device=args.device,
    )


if __name__ == "__main__":
    main()
