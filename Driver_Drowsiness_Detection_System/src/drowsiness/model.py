"""MobileNetV2 + classification head, and the fine-tuning switch used in phase 2."""
from __future__ import annotations

from tensorflow import keras
from tensorflow.keras import layers

from .config import Config


def build_model(cfg: Config, weights: str | None = "imagenet") -> tuple[keras.Model, keras.Model]:
    """Return ``(model, backbone)``. Input is a 0-1 float image; a Rescaling layer maps it to [-1, 1] for MobileNetV2.

    The backbone starts frozen and is always called with ``training=False``, so its BatchNorm layers keep their
    ImageNet statistics, also during fine-tuning. ``weights=None`` gives a randomly initialised backbone (tests).
    """
    base = keras.applications.MobileNetV2(input_shape=(cfg.img_size, cfg.img_size, 3), include_top=False, weights=weights)
    base.trainable = False
    inputs = keras.Input((cfg.img_size, cfg.img_size, 3), name="face_0_1")
    x = layers.Rescaling(2.0, offset=-1.0, name="to_minus1_1")(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(cfg.dropout)(x)
    x = layers.Dense(cfg.head_units, activation="relu")(x)
    x = layers.Dropout(cfg.dropout)(x)
    outputs = layers.Dense(1, activation="sigmoid", name="p_drowsy")(x)
    return keras.Model(inputs, outputs, name="drowsiness_mobilenetv2"), base


def compile_model(model: keras.Model, lr: float) -> None:
    """Adam + binary cross-entropy with accuracy, precision, recall and AUC. Call again after changing ``trainable``."""
    model.compile(optimizer=keras.optimizers.Adam(lr), loss="binary_crossentropy",
                  metrics=["accuracy", keras.metrics.Precision(name="precision"), keras.metrics.Recall(name="recall"),
                           keras.metrics.AUC(name="auc")])


def unfreeze_top_layers(base: keras.Model, n_last: int) -> None:
    """Phase-2 setting: only the last ``n_last`` backbone layers train, and every BatchNorm layer stays frozen."""
    base.trainable = True
    for layer in base.layers[:-n_last]:
        layer.trainable = False
    for layer in base.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False
