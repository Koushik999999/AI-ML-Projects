import cv2
import numpy as np
import pandas as pd

from lpblur.dataset import audit_dataset, base_name, clean_dataset, find_leakage, source_bases, write_data_yaml
from lpblur.evaluate import iou_mat, recall_by_size


def test_base_name_strips_augmentation_suffix():
    assert base_name("car1_jpg.rf.0284e407.jpg") == "car1"
    assert base_name("plain.jpg") == "plain"


def test_iou_mat():
    a = np.array([[0, 0, 10, 10]], dtype=float)
    b = np.array([[0, 0, 10, 10], [5, 0, 15, 10], [20, 20, 30, 30]], dtype=float)
    assert np.allclose(iou_mat(a, b), [[1.0, 1 / 3, 0.0]])
    assert iou_mat(np.zeros((0, 4)), b).shape == (0, 3)


def test_recall_by_size():
    hits = pd.DataFrame({"img": list("abcd"), "hit": [True, False, True, True], "w_px": [10, 15, 50, 60]})
    tab = recall_by_size(hits)
    assert tab.loc["< 20 px", "plates"] == 2 and tab.loc["< 20 px", "recall"] == 0.5
    assert tab.loc["< 20 px", "missed"] == 1 and tab.loc["40-80 px", "recall"] == 1.0


def _write(root, split, name, label):
    (root / "images" / split).mkdir(parents=True, exist_ok=True)
    (root / "labels" / split).mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(root / "images" / split / f"{name}.jpg"), np.zeros((20, 40, 3), np.uint8))
    if label is not None:
        (root / "labels" / split / f"{name}.txt").write_text(label)


def test_audit_leakage_and_clean(tmp_path):
    ok = "0 0.5 0.5 0.2 0.2\n"
    _write(tmp_path, "train", "a_jpg.rf.x1", ok)
    _write(tmp_path, "train", "a_jpg.rf.x2", ok)
    _write(tmp_path, "train", "nolabel", None)
    _write(tmp_path, "train", "empty", "")
    _write(tmp_path, "val", "a_jpg.rf.v", ok)  # same source photo as train -> leak
    _write(tmp_path, "val", "b_jpg.rf.v", ok)
    _write(tmp_path, "test", "c_jpg.rf.t", ok)

    df, problems, _ = audit_dataset(str(tmp_path))
    assert len(df) == 5 and {r for _, _, r in problems} == {"no label file", "empty label file"}
    assert find_leakage(source_bases(df))["train&val"] == {"a"}

    removed = tmp_path.parent / (tmp_path.name + "_removed")
    assert clean_dataset(str(tmp_path), str(removed)) == {"missing_or_empty_label": 2, "val_leaked_from_train": 1}
    assert sorted(p.name for p in (tmp_path / "images" / "val").iterdir()) == ["b_jpg.rf.v.jpg"]
    assert (removed / "images" / "val" / "a_jpg.rf.v.jpg").exists()  # moved, not deleted
    assert "license_plate" in open(write_data_yaml(str(tmp_path))).read()
