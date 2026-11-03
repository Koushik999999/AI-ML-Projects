"""The CLI parser, and every `python -m drowsiness ...` / demo command quoted in the README."""
import importlib.util
import re
import shlex
from pathlib import Path

import pytest

from drowsiness.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FENCE = "`" * 3


def test_parser_overrides():
    a = build_parser().parse_args(["train", "--subset", "0.04", "--epochs-p1", "1", "--epochs-p2", "1", "--detector", "haar", "--seed", "7"])
    assert (a.subset, a.epochs_p1, a.epochs_p2, a.detector, a.seed) == (0.04, 1, 1, "haar", 7)


def test_predict_defaults_point_at_the_shipped_model():
    a = build_parser().parse_args(["predict", "img.png"])
    assert a.model.name == "drowsiness_float16.tflite" and a.metadata.name == "metadata.json"


def test_invalid_detector_is_rejected():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["prepare", "--detector", "mtcnn"])


def _readme_lines(prefix):
    text = README.read_text(encoding="utf-8")
    for block in re.findall(FENCE + r"(?:bash|powershell)\n(.*?)" + FENCE, text, flags=re.S):
        for line in block.splitlines():
            if line.strip().startswith(prefix):
                yield shlex.split(line.strip().removeprefix(prefix))


@pytest.mark.skipif(not README.exists(), reason="README not written yet")
def test_every_readme_cli_command_parses():
    commands = list(_readme_lines("python -m drowsiness "))
    assert commands, "README lists no `python -m drowsiness` commands"
    for argv in commands:
        build_parser().parse_args(argv)   # raises SystemExit on unknown flags


@pytest.mark.skipif(not README.exists(), reason="README not written yet")
def test_every_readme_demo_command_parses():
    spec = importlib.util.spec_from_file_location("demo_video", ROOT / "scripts" / "demo_video.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    commands = list(_readme_lines("python scripts/demo_video.py "))
    assert commands
    for argv in commands:
        demo.parse_args(argv)
