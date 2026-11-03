"""Two-phase training: frozen-backbone head training, then fine-tuning of the last backbone layers."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from tensorflow import keras

from . import plots
from .config import Config
from .data import Dataset, class_weights, make_dataset, split_indices
from .model import build_model, compile_model, unfreeze_top_layers

BEST_MODEL = "best_model.keras"


def _callbacks(cfg: Config, best_path: Path, initial_best: float | None = None, min_lr: float = 1e-6) -> list[keras.callbacks.Callback]:
    """Early stopping and LR reduction on validation loss; the checkpoint only overwrites a file if it is a new best."""
    return [keras.callbacks.EarlyStopping("val_loss", patience=cfg.es_patience, restore_best_weights=True, verbose=1),
            keras.callbacks.ReduceLROnPlateau("val_loss", factor=cfg.lr_factor, patience=cfg.lr_patience, min_lr=min_lr, verbose=1),
            keras.callbacks.ModelCheckpoint(best_path, monitor="val_loss", save_best_only=True, initial_value_threshold=initial_best, verbose=0)]


def train(cfg: Config, ds: Dataset, out_dir: Path) -> pd.DataFrame:
    """Train with the validation split carved from train/ (the test folder is never touched). Returns the epoch history.

    Writes ``best_model.keras`` (best validation loss over both phases), ``history.csv``, ``training_curves.png`` and
    ``train_summary.json`` into ``out_dir``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    keras.utils.set_random_seed(cfg.seed)

    tr_idx, va_idx, _ = split_indices(ds, cfg)
    train_ds = make_dataset(ds.X[tr_idx], ds.y[tr_idx], cfg, training=True)
    val_ds = make_dataset(ds.X[va_idx], ds.y[va_idx], cfg, training=False)
    weights = class_weights(ds.y[tr_idx])
    print(f"train {len(tr_idx)} | val {len(va_idx)} images | class weights used: {weights is not None}")

    best_path = out_dir / BEST_MODEL
    model, base = build_model(cfg)
    compile_model(model, cfg.p1_lr)

    print(f"=== Phase 1: frozen base, lr = {cfg.p1_lr}")
    t0 = time.time()
    h1 = model.fit(train_ds, validation_data=val_ds, epochs=cfg.p1_epochs, class_weight=weights, callbacks=_callbacks(cfg, best_path), verbose=2)
    t_phase1 = time.time() - t0

    unfreeze_top_layers(base, cfg.unfreeze_last)
    compile_model(model, cfg.p2_lr)                      # recompile so the new trainable flags take effect
    n_trainable = sum(int(np.prod(w.shape)) for w in model.trainable_weights)
    print(f"=== Phase 2: {n_trainable:,} trainable parameters (of {model.count_params():,}), lr = {cfg.p2_lr}")
    t0 = time.time()
    h2 = model.fit(train_ds, validation_data=val_ds, epochs=cfg.p2_epochs, class_weight=weights,
                   callbacks=_callbacks(cfg, best_path, initial_best=min(h1.history["val_loss"]), min_lr=1e-7), verbose=2)
    t_phase2 = time.time() - t0

    hist = pd.concat([pd.DataFrame(h1.history).assign(phase="1: head only"), pd.DataFrame(h2.history).assign(phase="2: fine-tune")], ignore_index=True)
    hist.index.name = "epoch"; hist.index += 1
    hist.to_csv(out_dir / "history.csv")
    plots.training_curves(hist, len(h1.history["loss"]) + 0.5, out_dir / "training_curves.png")

    summary = {"config": {k: v for k, v in cfg.__dict__.items()}, "n_train": len(tr_idx), "n_val": len(va_idx),
               "best_val_loss": float(hist.val_loss.min()), "best_epoch": int(hist.val_loss.idxmin()),
               "phase1_seconds": round(t_phase1), "phase2_seconds": round(t_phase2), "total_minutes": round((t_phase1 + t_phase2) / 60, 1)}
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Best epoch {summary['best_epoch']} with val_loss {summary['best_val_loss']:.4f} | total {summary['total_minutes']} min | saved {best_path}")
    return hist

