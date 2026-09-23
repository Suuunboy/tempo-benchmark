from __future__ import annotations
import numpy as np

class LibrosaReference:
    name = "Librosa (reference)"
    is_realtime = False

    def __init__(self) -> None:
        self._buffer: list[np.ndarray] = []
        self._sample_rate: float = 0.0
        self._current_bpm: float = 0.0

    def reset(self, sample_rate: float) -> None:
        self._buffer = []
        self._sample_rate = float(sample_rate)
        self._current_bpm = 0.0

    def process_block(self, samples: np.ndarray) -> None:
        # Detection is not real-time, so just accumulate the samples
        self._buffer.append(np.asarray(samples, dtype=np.float32).copy())

    def get_bpm(self) -> float:
        return self._current_bpm

    def finalize(self) -> float:
        import librosa

        if not self._buffer:
            return 0.0
        y = np.concatenate(self._buffer)

        # Estimate BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=int(self._sample_rate))
        self._current_bpm = float(np.asarray(tempo).flatten()[0])
        return self._current_bpm
