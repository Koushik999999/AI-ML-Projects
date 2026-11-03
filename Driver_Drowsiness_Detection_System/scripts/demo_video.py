"""Real-time drowsiness demo on a webcam or a video file.

Per frame: face crop -> TFLite P(drowsy) -> rolling mean over ``smooth_window`` frames -> ALERT when the mean reaches the
threshold. Frames without a face are not classified; after a few seconds without a face the state becomes
"DRIVER ABSENT / NO FACE".

    python scripts/demo_video.py 0                      # webcam index 0
    python scripts/demo_video.py clip.mp4 --no-display --output annotated.mp4
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))   # lets the script run without `pip install -e .`

from drowsiness.config import DEFAULT_METADATA, DEFAULT_MODEL, DETECTORS   # noqa: E402
from drowsiness.faces import crop_to_box   # noqa: E402
from drowsiness.monitor import ABSENT, ALERT, NO_FACE, OK, WARMING_UP, DrowsinessMonitor   # noqa: E402
from drowsiness.predict import TFLiteClassifier   # noqa: E402

COLOURS = {OK: (0, 180, 0), WARMING_UP: (200, 200, 0), ALERT: (0, 0, 255), NO_FACE: (0, 165, 255), ABSENT: (0, 0, 255)}   # BGR
TEXT = {OK: "OK", WARMING_UP: "WARMING UP", ALERT: "DROWSY ALERT", NO_FACE: "NO FACE", ABSENT: "DRIVER ABSENT / NO FACE"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="webcam index (e.g. 0) or path to a video file")
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    p.add_argument("--detector", choices=DETECTORS, default=None)
    p.add_argument("--threshold", type=float, default=None, help="override the threshold from the metadata")
    p.add_argument("--window", type=int, default=None, help="smoothing window in frames (default: from the metadata, 10)")
    p.add_argument("--absent-seconds", type=float, default=3.0, help="seconds without a face before the absent state")
    p.add_argument("--no-display", action="store_true", help="do not open a window (headless); use with --output")
    p.add_argument("--output", type=Path, default=None, help="write the annotated video to this file")
    p.add_argument("--max-frames", type=int, default=None, help="stop after N frames")
    return p.parse_args(argv)


def annotate(frame, box, state, p_raw, smoothed, thr):
    """Draw the face box and a status banner."""
    colour = COLOURS[state]
    if box is not None:
        cv2.rectangle(frame, box[:2], box[2:], colour, 2)
    s = min(1.0, frame.shape[1] / 640)   # shrink the text on small frames
    cv2.rectangle(frame, (0, 0), (frame.shape[1], int(58 * s)), (30, 30, 30), -1)
    cv2.putText(frame, TEXT[state], (8, int(26 * s)), cv2.FONT_HERSHEY_SIMPLEX, 0.9 * s, colour, 1 + (s > 0.6), cv2.LINE_AA)
    raw = "-" if p_raw is None else f"{p_raw:.2f}"
    avg = "-" if smoothed is None else f"{smoothed:.2f}"
    cv2.putText(frame, f"raw {raw} | smoothed {avg} | thr {thr}", (8, int(50 * s)), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * s, (255, 255, 255), 1, cv2.LINE_AA)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    clf = TFLiteClassifier(args.model, args.metadata, args.detector, args.threshold)
    monitor = DrowsinessMonitor(clf.threshold, args.window or clf.meta["smooth_window"], args.absent_seconds)

    is_webcam = args.source.isdigit()
    cap = cv2.VideoCapture(int(args.source) if is_webcam else args.source)
    if not cap.isOpened():
        print(f"cannot open video source: {args.source}", file=sys.stderr)
        return 1
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = None
    counts: Counter[str] = Counter()
    t_start, frame_idx = time.monotonic(), 0

    while args.max_frames is None or frame_idx < args.max_frames:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        t = time.monotonic() - t_start if is_webcam else frame_idx / fps    # video files: timestamps follow the frame index
        box = clf.detector.detect(rgb)
        p_raw = None
        if box is not None:
            face = cv2.resize(crop_to_box(rgb, box, clf.detector.face_margin), (clf.img_size, clf.img_size), interpolation=cv2.INTER_AREA)
            p_raw = clf.predict_face(face)
        result = monitor.update(p_raw, t)
        counts[result.state] += 1
        frame_idx += 1

        annotate(bgr, box, result.state, p_raw, result.smoothed, clf.threshold)
        if args.output is not None:
            if writer is None:
                writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (bgr.shape[1], bgr.shape[0]))
            writer.write(bgr)
        if not args.no_display:
            cv2.imshow("Driver drowsiness demo (q to quit)", bgr)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if writer is not None:
        writer.release()
    if not args.no_display:
        cv2.destroyAllWindows()
    print(f"{frame_idx} frames in {time.monotonic() - t_start:.1f}s | state counts: {dict(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
