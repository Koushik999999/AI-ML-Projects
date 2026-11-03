"""Frame-stream logic: rolling-mean smoothing, the alert decision and the "driver absent / no face" state."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

WARMING_UP, OK, ALERT, NO_FACE, ABSENT = "warming_up", "ok", "alert", "no_face", "absent"


@dataclass(frozen=True)
class MonitorState:
    """Output of one monitor update."""

    state: str                      # warming_up | ok | alert | no_face (briefly) | absent (after ``absent_seconds``)
    smoothed: float | None          # rolling mean of P(drowsy); None until the window is full or while no face is visible


class DrowsinessMonitor:
    """Turns per-frame P(drowsy) values into an alert.

    An alert needs a full window of ``window`` face frames whose mean is >= ``threshold`` (acting on a single frame is
    noisy: blinks, glare). Frames without a face are passed as ``None``; after ``absent_seconds`` without any face the
    state becomes ``absent`` (camera blocked or driver gone) and the window is cleared.
    """

    def __init__(self, threshold: float, window: int = 10, absent_seconds: float = 3.0) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self.threshold, self.window, self.absent_seconds = threshold, window, absent_seconds
        self._probs: deque[float] = deque(maxlen=window)
        self._no_face_since: float | None = None

    def update(self, p_drowsy: float | None, t: float) -> MonitorState:
        """Feed one frame: its P(drowsy), or None if no face was found, and its timestamp ``t`` in seconds."""
        if p_drowsy is None:
            if self._no_face_since is None:
                self._no_face_since = t
            if t - self._no_face_since >= self.absent_seconds:
                self._probs.clear()
                return MonitorState(ABSENT, None)
            return MonitorState(NO_FACE, None)
        self._no_face_since = None
        self._probs.append(p_drowsy)
        if len(self._probs) < self.window:
            return MonitorState(WARMING_UP, None)
        mean = sum(self._probs) / self.window
        return MonitorState(ALERT if mean >= self.threshold else OK, mean)
