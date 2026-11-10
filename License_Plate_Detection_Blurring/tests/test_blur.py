import cv2
import numpy as np

from lpblur.blur import anonymize, blur_plates, detect, padded_box
from lpblur.video import blur_video


def _noise(h=200, w=300, seed=0):
    return np.random.default_rng(seed).integers(0, 256, (h, w, 3), dtype=np.uint8)


def _mask(boxes, w, h, pad):
    m = np.zeros((h, w), bool)
    for b in boxes:
        x1, y1, x2, y2 = padded_box(*b, w, h, pad)
        m[y1:y2, x1:x2] = True
    return m


def test_pixels_outside_padded_boxes_unchanged_and_inside_changed():
    img = _noise()
    boxes = np.array([[50, 60, 120, 100], [200, 120, 280, 180]], dtype=float)
    out = blur_plates(img, boxes, pad=0.08)
    mask = _mask(boxes, 300, 200, 0.08)
    changed = (img != out).any(axis=2)
    assert not changed[~mask].any()
    assert changed[mask].mean() > 0.9  # noise is smoothed almost everywhere inside the boxes


def test_input_not_modified_and_no_boxes_is_identity():
    img = _noise()
    before = img.copy()
    blur_plates(img, np.array([[10, 10, 80, 60]], dtype=float))
    assert np.array_equal(img, before)
    assert np.array_equal(blur_plates(img, np.zeros((0, 4))), img)


def test_padded_box_pads_and_clamps_to_image():
    assert padded_box(100, 100, 200, 150, 1000, 1000, 0.08) == (92, 96, 208, 154)
    assert padded_box(2, 2, 50, 50, 60, 60, 0.5) == (0, 0, 60, 60)


def test_degenerate_box_is_skipped():
    img = _noise()
    assert np.array_equal(blur_plates(img, np.array([[10, 10, 11, 11]], dtype=float), pad=0.0), img)


class _Cpu:
    def __init__(self, a):
        self.a = a

    def cpu(self):
        return self

    def numpy(self):
        return self.a


class _StubModel:
    """Minimal stand-in for an ultralytics model: always 'detects' one fixed plate."""

    def predict(self, img, conf, imgsz, verbose):
        boxes = type("B", (), {"xyxy": _Cpu(np.array([[50.0, 60.0, 120.0, 100.0]]))})()
        return [type("R", (), {"boxes": boxes})()]


def test_detect_and_anonymize_with_stub_model(tmp_path):
    img = _noise()
    path = str(tmp_path / "x.png")
    cv2.imwrite(path, img)
    assert detect(_StubModel(), img).shape == (1, 4)
    original, blurred, boxes = anonymize(path, _StubModel())
    assert len(boxes) == 1 and not np.array_equal(original, blurred)


def test_blur_video_roundtrip(tmp_path):
    src, dst = str(tmp_path / "in.mp4"), str(tmp_path / "out.mp4")
    vw = cv2.VideoWriter(src, cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    for i in range(5):
        vw.write(_noise(240, 320, seed=i))
    vw.release()
    n, fps = blur_video(src, dst, _StubModel())
    assert n == 5 and fps > 0
    cap = cv2.VideoCapture(dst)
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 5
    cap.release()


def test_hide_plates_covers_exactly_the_blurred_region():
    from lpblur.viz import hide_plates

    img = _noise()
    boxes = np.array([[50, 60, 120, 100]], dtype=float)
    hidden = hide_plates(img, boxes, pad=0.08)
    mask = _mask(boxes, 300, 200, 0.08)
    assert (hidden[mask] == 0).all()
    assert np.array_equal(hidden[~mask], img[~mask])
