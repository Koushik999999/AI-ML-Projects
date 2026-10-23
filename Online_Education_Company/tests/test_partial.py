"""Partial recordings (clips, late starts, truncated analysis): opening-only / closing-only checks are not assessable."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.assess import assess  # noqa: E402
from src.features.transcript import transcript_features  # noqa: E402
from src.scoring.explain import observations  # noqa: E402
from src.scoring.partial import partial_info  # noqa: E402
from src.scoring.rubric import score  # noqa: E402
from src.vtt import Cue  # noqa: E402


def _cues(start=0.0, minutes=10, greeting=False, homework=False):
    """Teacher/child exchange with NO praise, rapport, recap, homework or goodbye unless asked for."""
    out = []
    t = start
    if greeting:
        out += [Cue(t, t + 3, "T", "Hello, how are you today?"), Cue(t + 4, t + 5, "K", "Fine sir")]
    for i in range(int(minutes * 60 // 12)):
        out += [Cue(t + 10 + i * 12, t + 15 + i * 12, "T", "Now move the knight two squares, can you do it?"),
                Cue(t + 16 + i * 12, t + 17 + i * 12, "K", "Yes I move here")]
    if homework:
        out.append(Cue(t + minutes * 60 - 5, t + minutes * 60 - 1, "T", "Your homework is page two. Bye, see you next class."))
    return out


def _features(duration_s, start=0.0, minutes=10, truncated=False, **kw):
    return {"media": {"duration_s": duration_s, "truncated": truncated},
            "transcript": transcript_features(_cues(start, minutes, **kw), duration_s) | {"source": "vtt"},
            "audio": {}, "video": {}}


def test_full_class_is_not_partial():
    p = partial_info(_features(45 * 60, minutes=40))
    assert not p.is_partial and p.not_assessable == []


def test_short_clip_late_start_and_truncation_are_detected_independently():
    short = partial_info(_features(10 * 60))
    assert short.skip_opening and short.skip_closing and "10 min" in short.reasons[0]
    late = partial_info(_features(60 * 60, start=15 * 60, minutes=30))
    assert late.skip_opening and late.skip_closing
    cut = partial_info(_features(120 * 60, minutes=40, truncated=True))
    assert cut.skip_closing and not cut.skip_opening          # only the END is missing
    assert set(short.not_assessable) == {"rapport check-in", "greeting", "new-joiner introduction", "homework", "recap", "closing"}


def test_partial_score_ignores_absent_opening_and_closing_but_full_class_is_penalised():
    clip_bare = _features(10 * 60)                                   # no greeting / homework in a 10-minute clip
    clip_rich = _features(10 * 60)
    for k in ("has_rapport", "has_greeting", "has_new_joiner_intro", "has_homework", "has_recap", "has_closing"):
        clip_rich["transcript"][k] = True                            # identical features except the opening/closing flags
    assert score(clip_bare).overall == score(clip_rich).overall      # not assessable -> neither rewarded nor punished
    assert score(clip_bare).dimensions["Rapport & opening"] is None  # whole dimension dropped and the rest reweighted
    # per-minute signals still count in the dimension that remains
    assert score(clip_bare).dimensions["Structure & clarity"] is not None
    full_bare = _features(45 * 60, minutes=40)
    full_rich = _features(45 * 60, minutes=40)
    for k in ("has_rapport", "has_greeting", "has_new_joiner_intro", "has_homework", "has_recap", "has_closing"):
        full_rich["transcript"][k] = True
    assert score(full_rich).overall > score(full_bare).overall       # on a full class the same absence DOES matter


def test_partial_lowers_confidence():
    short, full = _features(10 * 60), _features(45 * 60, minutes=10)
    assert score(short).confidence < score(full).confidence


def test_items_marked_not_assessable_and_no_opening_closing_observations():
    f = _features(10 * 60)
    items = {i["item"]: i for i in score(f).items["Rapport & opening"] + score(f).items["Structure & clarity"]}
    for name in ("rapport question in opening", "greeting", "homework given", "recap", "closing"):
        assert items[name]["not_assessable"] and items[name]["score"] is None
    text = " ".join(o.text for o in observations(f, [], "T"))
    assert "rapport" not in text.lower() and "homework" not in text.lower() and "recap or a closing" not in text
    # the same recording treated as a full class WOULD report them (so the test is meaningful)
    full_text = " ".join(o.text for o in observations(_features(45 * 60, minutes=10), [], "T"))
    assert "rapport" in full_text.lower() and "homework" in full_text.lower()


def test_truncated_analysis_keeps_opening_checks():
    f = _features(120 * 60, minutes=40, truncated=True, greeting=True)
    sc = score(f)
    assert sc.dimensions["Rapport & opening"] is not None
    items = {i["item"]: i for i in sc.items["Structure & clarity"]}
    assert items["homework given"]["not_assessable"] and not items["checks understanding"]["not_assessable"]


def test_assess_adds_partial_banner():
    r = assess(_features(10 * 60))
    assert r["partial"]["is_partial"] and "closing" in r["partial"]["not_assessable"]
    assert r["notes"][0].startswith("This looks like a PARTIAL class")
    assert not assess(_features(45 * 60, minutes=40))["partial"]["is_partial"]
