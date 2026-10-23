import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.scoring.rubric import band, label_for, ramp, score  # noqa: E402
from src.scoring.technical import technical_report  # noqa: E402
from src.vtt import parse_vtt  # noqa: E402
from src.features.transcript import pick_teacher, transcript_features  # noqa: E402
from src.scoring.explain import anonymise  # noqa: E402


def test_ramp_directions():
    assert ramp(5, 0, 10) == 0.5
    assert ramp(-1, 0, 10) == 0.0 and ramp(99, 0, 10) == 1.0
    assert ramp(0.2, 2.0, 0.6) == 1.0          # lower is better
    assert ramp(None, 0, 1) is None


def test_band():
    assert band(0.5, 0.9, 0.4, 0.65, 0.95) == 1.0
    assert band(0.95, 0.9, 0.4, 0.65, 0.95) == 0.0


def test_labels_monotonic():
    cuts = (40, 52, 64)
    assert [label_for(x, cuts) for x in (10, 45, 60, 90)] == ["Poor", "Average", "Good", "Excellent"]


def _vtt(lines):
    out = ["WEBVTT", ""]
    for i, (s, e, spk, txt) in enumerate(lines, 1):
        out += [str(i), f"00:{s // 60:02d}:{s % 60:02d}.000 --> 00:{e // 60:02d}:{e % 60:02d}.000", f"{spk}: {txt}", ""]
    return "\n".join(out)


def test_vtt_and_teacher_and_features():
    rows = [(1, 4, "Ms T", "Hello, how are you today?"), (5, 6, "Kid A", "Fine ma'am thank you"),
            (7, 12, "Ms T", "Great! Today we learn the knight. Understood?"), (13, 14, "Kid B", "Yes"),
            (15, 17, "Ms T", "Very good. Homework is page two."), (19, 20, "Ms T", "Bye, see you next class.")]
    cues = parse_vtt(_vtt(rows))
    assert len(cues) == 6 and cues[0].speaker == "Ms T"
    assert pick_teacher(cues) == "Ms T"
    f = transcript_features(cues)
    assert f["has_rapport"] and f["has_homework"] and f["has_closing"]
    assert f["n_students_spoke"] == 2 and 0 < f["teacher_talk_share"] < 1


def test_score_more_interaction_scores_higher():
    base = {"transcript": {"ok": True, "has_speakers": True, "n_students_asked_individually": 1, "student_turns_per_min": 2.0,
                           "student_top_share": 0.7, "median_response_latency_s": 2.0, "praise_per_10min": 1.0}}
    good = {"transcript": dict(base["transcript"], n_students_asked_individually=6, student_turns_per_min=8.0,
                               student_top_share=0.3, median_response_latency_s=0.5, praise_per_10min=8.0)}
    assert score(good).overall > score(base).overall
    assert score(good).dimensions["Individual interaction"] == 100.0


def test_missing_data_does_not_crash_and_lowers_confidence():
    s = score({})
    assert s.coverage == 0 and s.label == "Poor"


def test_platform_fault_excludes_presentation():
    f = {"audio": {"ok": True, "dropouts": [{"start": 10, "end": 14}], "clipping_ratio": 0.0, "median_speech_db": -25},
         "video": {"ok": True, "frozen_runs": [{"start": 60, "end": 120}], "camera_off_runs": [], "dim_face_ratio": 0.0, "face_ratio": 0.5, "screen_ratio": 0.4}}
    r = technical_report(f)
    assert r["exclude_presentation"] and len(r["platform"]) == 2


def test_anonymise_removes_names():
    out = anonymise("Good job Priya Nair, well done Priya!", ["Priya Nair", "Ms T"], "Ms T")
    assert "Priya" not in out and "Nair" not in out and "Student A" in out


def test_anonymise_redacts_asr_mangled_names():
    out = anonymise("ZORBA MENDLE, are you there? Hello Priya, good job Ravi! Okay let us start.", ["Ravi Kumar"], "Ms T")
    assert "ZORBA" not in out and "Priya" not in out and "Ravi" not in out
    assert "let us start" in out  # ordinary words are untouched


def test_confidence_low_when_borderline_and_capped_by_label():
    from src.scoring.rubric import confidence_for
    cuts = (42, 56, 72)
    far = confidence_for(88, "Excellent", cuts, 1.0)
    border = confidence_for(56.5, "Good", cuts, 1.0)
    assert far > 0.8 and border < 0.3                      # distance to cut-off matters
    assert confidence_for(10, "Poor", cuts, 1.0) <= 0.65   # weakly supported labels never look certain
    assert confidence_for(88, "Excellent", cuts, 0.4) <= 0.25   # missing signals cap confidence
    assert confidence_for(88, "Excellent", cuts, 1.0, 0.7) < far   # unreliable signals lower it
