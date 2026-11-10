import numpy as np
import pytest

from lpblur.coords import pixel_to_yolo, read_gt, yolo_to_pixel

CASES = [
    ((0.5, 0.5, 0.2, 0.1, 1000, 500), (400, 225, 600, 275)),  # centred box, non-square image
    ((0.05, 0.5, 0.2, 0.2, 100, 100), (0, 40, 15, 60)),  # clamped at the left border
    ((0.95, 0.5, 0.2, 0.2, 100, 100), (85, 40, 99, 60)),  # clamped at the right border (W-1)
    ((0.25, 0.75, 0.1, 0.2, 640, 480), (128, 312, 192, 408)),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_yolo_to_pixel_known_cases(args, expected):
    assert yolo_to_pixel(*args) == expected


def test_clamps_all_four_borders():
    # a box larger than the image must clamp to [0, W-1] x [0, H-1]
    assert yolo_to_pixel(0.5, 0.5, 1.5, 1.5, 200, 100) == (0, 0, 199, 99)


def test_returns_python_ints():
    assert all(isinstance(v, int) for v in yolo_to_pixel(0.5, 0.5, 0.2, 0.1, 1000, 500))


def test_round_trip_error_below_one_pixel():
    rng = np.random.default_rng(0)
    for _ in range(1000):
        w_img, h_img = int(rng.integers(200, 1500)), int(rng.integers(200, 1500))
        w, h = rng.uniform(0.05, 0.4, 2)
        cx = rng.uniform(w / 2 + 0.01, 1 - w / 2 - 0.01)
        cy = rng.uniform(h / 2 + 0.01, 1 - h / 2 - 0.01)
        bcx, bcy, bw, bh = pixel_to_yolo(*yolo_to_pixel(cx, cy, w, h, w_img, h_img), w_img, h_img)
        assert abs(bcx - cx) * w_img <= 1 and abs(bcy - cy) * h_img <= 1
        assert abs(bw - w) * w_img <= 1.5 and abs(bh - h) * h_img <= 1.5


def test_read_gt(tmp_path):
    label = tmp_path / "a.txt"
    label.write_text("0 0.5 0.5 0.2 0.1\nbad line\n")
    boxes = read_gt(str(label), 1000, 500)
    assert boxes.shape == (1, 4)
    assert np.allclose(boxes[0], [400, 225, 600, 275])
    assert read_gt(str(tmp_path / "missing.txt"), 100, 100).shape == (0, 4)
