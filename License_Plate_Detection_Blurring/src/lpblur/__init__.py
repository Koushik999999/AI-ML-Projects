"""License plate detection and automatic blurring (YOLOv8s, recall-first)."""

__version__ = "0.1.0"

DEFAULT_CONF = 0.10  # low threshold: a missed plate is a privacy leak, a false blur is cheap
DEFAULT_PAD = 0.08  # each detected box is enlarged by 8% before blurring
DEFAULT_IMGSZ = 640
DEFAULT_SEED = 42
