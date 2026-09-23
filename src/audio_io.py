from __future__ import annotations
from typing import Tuple

import numpy as np


# 22050 Hz is the librosa default: enough for BPM detection and faster to process
DEFAULT_SR = 22050


def generate_click_track(
    bpm: float = 120.0,
    duration_sec: float = 12.0,
    sample_rate: int = DEFAULT_SR,
    click_freq: float = 1500.0,
    noise_level: float = 0.0,
) -> Tuple[np.ndarray, int]:
    """Generate a synthetic click track.

    Each beat is a short tone burst with a fast exponential decay.
    Optional white noise helps to emulate a "dirty" signal.
    """
    period_sec = 60.0 / bpm
    n_samples = int(duration_sec * sample_rate)
    y = np.zeros(n_samples, dtype=np.float32)

    click_len = int(0.04 * sample_rate)  # 40 ms click
    t = np.arange(click_len) / sample_rate
    envelope = np.exp(-t * 60.0)
    click = (np.sin(2 * np.pi * click_freq * t) * envelope).astype(np.float32) * 0.6

    samples_per_beat = period_sec * sample_rate
    beat = 0
    while True:
        idx = int(beat * samples_per_beat)
        end = idx + click_len
        if end > n_samples:
            break
        y[idx:end] += click
        beat += 1

    if noise_level > 0:
        rng = np.random.default_rng(42)
        y += rng.standard_normal(n_samples).astype(np.float32) * noise_level

    return y, sample_rate


def load_audio(path: str, target_sr: int = DEFAULT_SR) -> Tuple[np.ndarray, int]:
    """Load an audio file and convert it to mono float32 at ``target_sr``.

    Supports any format that librosa + soundfile understand
    (.wav, .mp3, .flac, .ogg, .m4a, ...).
    """
    import librosa

    y, sr = librosa.load(path, sr=target_sr, mono=True)
    return y.astype(np.float32), int(sr)
