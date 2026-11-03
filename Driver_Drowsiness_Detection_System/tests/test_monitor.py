"""Rolling-mean alert and driver-absent logic on synthetic probability streams."""
import pytest

from drowsiness.monitor import ABSENT, ALERT, NO_FACE, OK, WARMING_UP, DrowsinessMonitor


def test_needs_a_full_window_before_deciding():
    m = DrowsinessMonitor(threshold=0.5, window=3)
    assert [m.update(0.9, t).state for t in range(2)] == [WARMING_UP, WARMING_UP]
    assert m.update(0.9, 2).state == ALERT


def test_a_single_spike_does_not_alert_but_a_sustained_signal_does():
    m = DrowsinessMonitor(threshold=0.5, window=4)
    states = [m.update(p, t).state for t, p in enumerate([0.0, 0.0, 0.0, 1.0, 0.0, 0.0])]
    assert ALERT not in states and states[-1] == OK
    m = DrowsinessMonitor(threshold=0.5, window=4)
    assert [m.update(0.8, t).state for t in range(5)][-1] == ALERT


def test_smoothed_value_is_the_rolling_mean():
    m = DrowsinessMonitor(threshold=0.5, window=2)
    m.update(0.2, 0)
    assert m.update(0.6, 1).smoothed == pytest.approx(0.4)
    assert m.update(1.0, 2).smoothed == pytest.approx(0.8)   # the window slides


def test_driver_absent_after_the_timeout_and_window_is_reset():
    m = DrowsinessMonitor(threshold=0.5, window=2, absent_seconds=3.0)
    m.update(0.9, 0)
    m.update(0.9, 1)
    assert m.update(None, 2).state == NO_FACE
    assert m.update(None, 4.9).state == NO_FACE
    assert m.update(None, 5.0).state == ABSENT
    assert m.update(0.9, 6).state == WARMING_UP          # a fresh window is needed once the driver is back


def test_short_face_loss_is_not_absence():
    m = DrowsinessMonitor(threshold=0.5, window=2, absent_seconds=3.0)
    m.update(0.1, 0)
    m.update(0.1, 1)
    assert m.update(None, 2).state == NO_FACE
    assert m.update(0.1, 3).state == OK


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError):
        DrowsinessMonitor(0.5, window=0)
