"""Command line interface: ``python -m drowsiness {prepare,train,evaluate,export,predict}``."""
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .config import DEFAULT_METADATA, DEFAULT_MODEL, DETECTORS, Config


def build_parser() -> argparse.ArgumentParser:
    """Argument parser for all sub-commands."""
    parser = argparse.ArgumentParser(prog="drowsiness", description="Driver drowsiness detection (MobileNetV2 + TFLite).")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", type=Path, default=Path("dataset"), help="folder with {train,test}/{drowsy,non_drowsy} (default: dataset)")
    common.add_argument("--out-dir", type=Path, default=Path("runs/latest"), help="where models, tables and figures are written (default: runs/latest)")
    common.add_argument("--cache-dir", type=Path, default=Path("cache"), help="cache of the preprocessed face crops (default: cache)")
    common.add_argument("--subset", type=float, default=None, help="stratified fraction of the data to use, e.g. 0.04 for a smoke test")
    common.add_argument("--detector", choices=DETECTORS, default=None, help="face detector: dlib (default), haar, or none (no crop)")
    common.add_argument("--seed", type=int, default=None, help="random seed (default 42)")

    p = sub.add_parser("prepare", parents=[common], help="detect and crop faces once and cache the arrays")
    p.add_argument("--force", action="store_true", help="recompute even if a cache exists")

    p = sub.add_parser("train", parents=[common], help="two-phase training, writes best_model.keras")
    p.add_argument("--epochs-p1", type=int, default=None, help="phase-1 epochs (default 12)")
    p.add_argument("--epochs-p2", type=int, default=None, help="phase-2 epochs (default 12)")
    p.add_argument("--batch-size", type=int, default=None, help="batch size (default 32)")

    sub.add_parser("evaluate", parents=[common], help="choose the threshold on validation, evaluate once on the test set")

    p = sub.add_parser("export", parents=[common], help="export TFLite variants and benchmark them")
    p.add_argument("--bench-limit", type=int, default=None, help="only benchmark the first N test images")

    p = sub.add_parser("predict", help="classify images with a TFLite model")
    p.add_argument("inputs", nargs="+", type=Path, help="image files or folders")
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="TFLite model (default: models/drowsiness_float16.tflite)")
    p.add_argument("--metadata", type=Path, default=DEFAULT_METADATA, help="metadata.json with threshold and preprocessing (default: models/metadata.json)")
    p.add_argument("--detector", choices=DETECTORS, default=None, help="override the detector from the metadata")
    p.add_argument("--threshold", type=float, default=None, help="override the threshold from the metadata")
    return parser


def _config(args: argparse.Namespace) -> Config:
    """Default configuration with the command-line overrides applied."""
    overrides = {"subset": args.subset, "detector": args.detector, "seed": args.seed, "p1_epochs": getattr(args, "epochs_p1", None),
                 "p2_epochs": getattr(args, "epochs_p2", None), "batch_size": getattr(args, "batch_size", None)}
    return replace(Config(), **{k: v for k, v in overrides.items() if v is not None})


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_parser().parse_args(argv)

    if args.command == "predict":
        from .predict import TFLiteClassifier, collect_images
        clf = TFLiteClassifier(args.model, args.metadata, args.detector, args.threshold)
        for path in collect_images(args.inputs):
            r = clf.predict_path(path)
            note = "" if r.face_found else "  (no face found: whole image used)"
            print(f"{r.path.name}\t{r.label}\tP(drowsy)={r.p_drowsy:.4f}\tthreshold={r.threshold}{note}")
        return 0

    from .data import prepare
    cfg = _config(args)
    ds = prepare(cfg, args.data_dir, args.cache_dir, force=getattr(args, "force", False))
    if args.command == "train":
        from .train import train
        train(cfg, ds, args.out_dir)
    elif args.command == "evaluate":
        from .evaluate import evaluate
        evaluate(cfg, ds, args.out_dir)
    elif args.command == "export":
        from .export_tflite import export
        export(cfg, ds, args.out_dir, args.bench_limit)
    return 0
