"""Driver drowsiness detection: MobileNetV2 transfer learning with face cropping and TensorFlow Lite export."""
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")   # keep the console readable; must be set before TensorFlow is imported

__version__ = "0.1.0"
