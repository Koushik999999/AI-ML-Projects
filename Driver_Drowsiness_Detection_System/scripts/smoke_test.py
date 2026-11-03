"""One-command smoke test: prepare -> train -> evaluate -> export on a tiny stratified subset (about 1 minute).

Everything is written to a temporary folder that is deleted afterwards, so no existing outputs are touched.
It checks that the pipeline runs end to end; the metrics of a 1-epoch model on ~400 images are meaningless.

    python scripts/smoke_test.py --data-dir dataset
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ["best_model.keras", "final_results.csv", "metrics.json", "tflite_comparison.csv", "metadata.json",
            "drowsiness_float32.tflite", "drowsiness_dynamic_range.tflite", "drowsiness_float16.tflite", "drowsiness_int8.tflite"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"))
    parser.add_argument("--subset", type=float, default=0.04)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="drowsiness_smoke_") as tmp:
        common = ["--data-dir", str(args.data_dir), "--out-dir", f"{tmp}/out", "--cache-dir", f"{tmp}/cache", "--subset", str(args.subset)]
        steps = [["prepare"], ["train", "--epochs-p1", "1", "--epochs-p2", "1"], ["evaluate"], ["export", "--bench-limit", "50"]]
        for step in steps:
            print(f"\n>>> python -m drowsiness {' '.join(step)}", flush=True)
            subprocess.run([sys.executable, "-m", "drowsiness", *step, *common], check=True, cwd=ROOT,
                           env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")})
        missing = [name for name in EXPECTED if not (Path(tmp) / "out" / name).exists()]
        if missing:
            print(f"smoke test FAILED, missing outputs: {missing}")
            return 1
    print("\nsmoke test passed: all stages ran and produced their outputs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
