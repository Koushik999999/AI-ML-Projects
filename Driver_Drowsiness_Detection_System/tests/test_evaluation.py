"""Metrics and the validation-set threshold rule on toy data."""
import numpy as np
import pytest

from drowsiness.evaluate import metrics_at, select_threshold


def test_metrics_at_counts_and_scores():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    p = np.array([0.9, 0.8, 0.4, 0.2, 0.6, 0.1, 0.1, 0.1])
    m = metrics_at(y, p, 0.5)
    assert (m["TP"], m["FN"], m["FP"], m["TN"]) == (2, 2, 1, 3)
    assert m["recall"] == pytest.approx(0.5)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["accuracy"] == pytest.approx(5 / 8)


def test_select_threshold_takes_the_highest_threshold_among_recall_ties():
    # drowsy scores 0.9 / 0.5 / 0.3, alert scores 0.2 / 0.1: precision is 1.0 for every threshold above 0.2 and recall
    # is 1.0 for every threshold <= 0.3, so the tie is broken towards the highest threshold, 0.3
    y = np.array([1, 1, 1, 0, 0])
    p = np.array([0.9, 0.5, 0.3, 0.2, 0.1])
    thr, sweep = select_threshold(y, p, min_precision=0.95)
    assert thr == pytest.approx(0.3)
    assert sweep.loc[sweep.threshold == thr, "recall"].item() == pytest.approx(1.0)


def test_select_threshold_respects_the_precision_floor():
    # an alert frame (0.5) outscores the weakest drowsy frame (0.3): catching all drowsy frames would cost precision
    y = np.array([1, 1, 1, 0, 0])
    p = np.array([0.9, 0.8, 0.3, 0.5, 0.1])
    thr, sweep = select_threshold(y, p, min_precision=0.95)
    assert sweep.loc[sweep.threshold == thr, "precision"].item() >= 0.95
    assert thr == pytest.approx(0.8)   # recall 2/3 at precision 1.0; any lower threshold admits the 0.5 alert frame


def test_select_threshold_warns_when_the_floor_is_unreachable():
    y = np.array([1, 0, 1, 0])
    p = np.array([0.2, 0.9, 0.1, 0.8])
    with pytest.warns(RuntimeWarning):
        thr, _ = select_threshold(y, p, min_precision=0.95)
    assert 0.0 < thr < 1.0
