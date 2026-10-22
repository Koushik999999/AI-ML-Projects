"""Tests for the no-transcript path. A FAKE model stands in for faster-whisper (the real one needs a model download),
so these verify chunking, offsets, the time cap and the failure fallback -- NOT recognition quality."""
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.asr import SR, WhisperUnavailable, transcribe_audio  # noqa: E402
from src.features.speakers import cluster_roles  # noqa: E402


class FakeModel:
    """Returns one 'segment' per call, 1-3 s into the window it was given."""

    def __init__(self, delay: float = 0.0, fail_after: int | None = None):
        self.calls, self.delay, self.fail_after = 0, delay, fail_after

    def transcribe(self, audio, **kw):
        self.calls += 1
        if self.fail_after is not None and self.calls > self.fail_after:
            raise RuntimeError("boom")
        time.sleep(self.delay)
        return [SimpleNamespace(start=1.0, end=3.0, text=f"window {self.calls}")], SimpleNamespace(language="en")


def test_chunks_and_offsets():
    audio = np.zeros(SR * 100, np.float32)                    # 100 s
    res = transcribe_audio(audio, model=FakeModel(), window_s=30)
    assert [round(c.start) for c in res.cues] == [1, 31, 61, 91]   # offsets added per window
    assert res.complete and res.language == "en"


def test_time_cap_returns_partial():
    audio = np.zeros(SR * 100, np.float32)
    res = transcribe_audio(audio, model=FakeModel(delay=0.3), window_s=10, deadline_s=0.5)
    assert 0 < len(res.cues) < 10 and not res.complete and res.covered_s < res.total_s


def test_failure_after_partial_progress_keeps_partial():
    audio = np.zeros(SR * 60, np.float32)
    res = transcribe_audio(audio, model=FakeModel(fail_after=1), window_s=20)
    assert len(res.cues) == 1 and not res.complete


def test_failure_on_first_window_raises_readable_error():
    with pytest.raises(WhisperUnavailable):
        transcribe_audio(np.zeros(SR * 30, np.float32), model=FakeModel(fail_after=0), window_s=10)


def test_missing_model_raises_unavailable(monkeypatch):
    import src.features.asr as asr
    monkeypatch.setattr(asr, "_MODELS", {})
    monkeypatch.setitem(sys.modules, "faster_whisper", None)   # simulate package missing
    with pytest.raises(WhisperUnavailable):
        asr.load_model("tiny")


def test_cluster_roles_separates_two_synthetic_voices_and_names_bigger_cluster_teacher():
    rng = np.random.default_rng(0)
    a = [rng.normal(0, 0.3, 6) + 3 for _ in range(30)]     # 30 long segments, one 'voice'
    b = [rng.normal(0, 0.3, 6) - 3 for _ in range(12)]     # 12 short ones, another 'voice'
    roles, sep = cluster_roles(a + b, [6.0] * 30 + [2.0] * 12)
    assert roles[:30] == ["Teacher"] * 30 and roles[30:] == ["Student"] * 12 and sep > 1


def test_too_few_segments_returns_all_teacher():
    roles, sep = cluster_roles([np.ones(3)] * 5, [1.0] * 5)
    assert set(roles) == {"Teacher"} and sep == 0.0
