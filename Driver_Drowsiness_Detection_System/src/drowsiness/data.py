"""Dataset indexing, cached preprocessing, train/validation/test split and the tf.data pipelines."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from tensorflow.keras import layers

from .config import CLASS_NAMES, Config
from .faces import FaceDetector, load_rgb

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def build_index(data_dir: Path) -> pd.DataFrame:
    """Index ``data_dir/{train,test}/{non_drowsy,drowsy}/*`` into a DataFrame (path, label, split, seq, frame).

    File names look like ``A0022.png``: a letter prefix (``seq``) and a frame-like number (``frame``). What the prefix
    means is not documented, so it is only used for the leakage analysis in the notebook.
    """
    rows = []
    for split in ("train", "test"):
        for label, cls in enumerate(CLASS_NAMES):
            folder = Path(data_dir) / split / cls
            if not folder.is_dir():
                raise FileNotFoundError(f"expected folder {folder} (layout: dataset/{{train,test}}/{{drowsy,non_drowsy}})")
            for p in sorted(folder.glob("*")):
                if p.suffix.lower() in _IMAGE_SUFFIXES:
                    match = re.fullmatch(r"([A-Za-z]+)(\d+)", p.stem)
                    prefix, number = match.groups() if match else ("", 0)
                    rows.append((p, label, split, prefix, int(number)))
    df = pd.DataFrame(rows, columns=["path", "label", "split", "seq", "frame"])
    df["class_name"] = df.label.map(dict(enumerate(CLASS_NAMES)))
    return df


def subsample(df: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    """Stratified (split x label) random fraction of the index; ``fraction=1`` returns it unchanged."""
    if fraction >= 1.0:
        return df
    parts = [g.sample(frac=fraction, random_state=seed) for _, g in df.groupby(["split", "label"])]
    return pd.concat(parts).reset_index(drop=True)


@dataclass
class Dataset:
    """Preprocessed images plus their index; ``X`` is (N, size, size, 3) uint8 in the row order of ``df``."""

    X: np.ndarray
    df: pd.DataFrame

    @property
    def y(self) -> np.ndarray:
        return self.df.label.to_numpy()


def cache_dir_for(cache_root: Path, cfg: Config) -> Path:
    """Folder of the cache entry for this detector / subset / seed / size."""
    return Path(cache_root) / f"{cfg.detector}_sub{cfg.subset:g}_seed{cfg.seed}_{cfg.img_size}"


def prepare(cfg: Config, data_dir: Path, cache_root: Path, force: bool = False) -> Dataset:
    """Run face detection/cropping once and cache the result (the slow step); reuse the cache on later calls."""
    data_dir = Path(data_dir)
    folder = cache_dir_for(cache_root, cfg)
    if (folder / "faces.npy").exists() and not force:
        return load_cache(folder, data_dir)

    df = subsample(build_index(Path(data_dir)), cfg.subset, cfg.seed)
    detector = FaceDetector(cfg.detector, cfg.face_pad, cfg.face_margin)
    t0 = time.time()
    faces, found, area = [], [], []
    for i, path in enumerate(df.path, 1):
        face, ok, frac = detector.preprocess(load_rgb(path), cfg.img_size)
        faces.append(face); found.append(ok); area.append(frac)
        if i % 1000 == 0:
            print(f"  preprocessed {i}/{len(df)} images ({time.time() - t0:.0f}s)")
    X = np.stack(faces)
    df = df.assign(face_found=found, face_area_frac=area)
    df["path"] = [Path(p).relative_to(data_dir).as_posix() for p in df.path]

    folder.mkdir(parents=True, exist_ok=True)
    np.save(folder / "faces.npy", X)
    df.to_csv(folder / "index.csv", index=False)
    (folder / "meta.json").write_text(json.dumps({"detector": detector.kind, "subset": cfg.subset, "seed": cfg.seed,
                                                  "img_size": cfg.img_size, "n_images": len(df)}, indent=2))
    print(f"Processed {len(df)} images in {time.time() - t0:.0f}s -> {X.shape} uint8, cached in {folder}")
    if detector.kind != "none":
        print(f"Face found by {detector.kind}: {np.mean(found):.1%} (others keep the original image)")
    return Dataset(X, df.assign(path=[Path(data_dir) / p for p in df.path]))


def load_cache(folder: Path, data_dir: Path) -> Dataset:
    """Load a cache entry written by :func:`prepare`."""
    df = pd.read_csv(Path(folder) / "index.csv", keep_default_na=False)
    df["path"] = [Path(data_dir) / p for p in df.path]
    return Dataset(np.load(Path(folder) / "faces.npy"), df)


def split_indices(ds: Dataset, cfg: Config) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stratified validation split carved from the train folder; the test folder is kept untouched."""
    is_train = (ds.df.split == "train").to_numpy()
    pool = np.flatnonzero(is_train)
    tr_idx, va_idx = train_test_split(pool, test_size=cfg.val_fraction, stratify=ds.y[pool], random_state=cfg.seed)
    return tr_idx, va_idx, np.flatnonzero(~is_train)


def class_weights(y_train: np.ndarray) -> dict[int, float] | None:
    """Balanced class weights, but only if the training set is actually imbalanced (ratio > 1.2); else None."""
    w = compute_class_weight("balanced", classes=np.array([0, 1]), y=y_train)
    return dict(enumerate(w)) if max(w) / min(w) > 1.2 else None


def build_augmentation(cfg: Config) -> keras.Sequential:
    """Flip, rotation, zoom and brightness augmentation (training set only)."""
    return keras.Sequential([
        layers.RandomFlip("horizontal", seed=cfg.seed),
        layers.RandomRotation(cfg.aug_rotation, fill_mode="reflect", seed=cfg.seed),
        layers.RandomZoom((-cfg.aug_zoom, cfg.aug_zoom), fill_mode="reflect", seed=cfg.seed),
        layers.RandomBrightness(cfg.aug_brightness, value_range=(0.0, 1.0), seed=cfg.seed),
    ], name="augmentation")


def make_dataset(X: np.ndarray, y: np.ndarray, cfg: Config, training: bool) -> tf.data.Dataset:
    """uint8 arrays -> batched float32 [0, 1] tensors; shuffled and augmented when ``training``."""
    autotune = tf.data.AUTOTUNE
    ds = tf.data.Dataset.from_tensor_slices((X, y.astype("float32")))
    if training:
        ds = ds.shuffle(len(X), seed=cfg.seed)
    ds = ds.batch(cfg.batch_size).map(lambda a, b: (tf.cast(a, tf.float32) / 255.0, b), num_parallel_calls=autotune)
    if training:
        augment = build_augmentation(cfg)
        ds = ds.map(lambda a, b: (tf.clip_by_value(augment(a, training=True), 0.0, 1.0), b), num_parallel_calls=autotune)
    return ds.prefetch(autotune)
