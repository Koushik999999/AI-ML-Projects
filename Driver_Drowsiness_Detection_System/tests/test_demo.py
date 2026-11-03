"""The demo script end to end on a synthetic video (no webcam, no dataset)."""
import importlib.util
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not (ROOT / "models" / "drowsiness_float16.tflite").exists(), reason="shipped model missing")
def test_video_without_faces_ends_in_the_absent_state(tmp_path, capsys):
    video = tmp_path / "noise.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 30, (96, 96))
    rng = np.random.default_rng(0)
    for _ in range(100):   # 3.33 s at 30 fps of face-free noise
        writer.write(rng.integers(0, 256, (96, 96, 3), dtype=np.uint8))
    writer.release()

    spec = importlib.util.spec_from_file_location("demo_video", ROOT / "scripts" / "demo_video.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    assert demo.main([str(video), "--detector", "none", "--no-display"]) == 0
    out = capsys.readouterr().out
    assert "100 frames" in out and "'no_face': 90" in out and "'absent': 10" in out


def test_missing_video_source_returns_an_error(tmp_path):
    spec = importlib.util.spec_from_file_location("demo_video", ROOT / "scripts" / "demo_video.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    assert demo.main([str(tmp_path / "missing.mp4"), "--no-display"]) == 1
