"""Optional Gradio demo: upload an image, get the plate-blurred image back, with a confidence slider.

Run from the project folder:  python demo/app.py --weights weights/best.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lpblur import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_PAD  # noqa: E402
from lpblur.blur import blur_plates, detect, load_model  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--pad", type=float, default=DEFAULT_PAD)
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    ap.add_argument("--share", action="store_true", help="create a public Gradio link")
    args = ap.parse_args()

    import gradio as gr

    model = load_model(args.weights)

    def run(image, conf):
        bgr = image[:, :, ::-1]  # Gradio gives RGB, the pipeline works on BGR
        boxes = detect(model, bgr, conf, args.imgsz)
        return blur_plates(bgr, boxes, args.pad)[:, :, ::-1], f"{len(boxes)} plate(s) blurred"

    gr.Interface(
        run,
        [gr.Image(type="numpy", label="Input"),
         gr.Slider(0.01, 0.9, value=DEFAULT_CONF, step=0.01, label="Confidence threshold (lower = fewer misses)")],
        [gr.Image(label="Blurred"), gr.Textbox(label="Result")],
        title="License plate blurring",
        allow_flagging="never",
    ).launch(share=args.share)


if __name__ == "__main__":
    main()
