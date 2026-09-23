import numpy as np
import pytest

import tempo_cpp
from src.audio_io import generate_click_track
from src.simulator import simulate_realtime

ALGORITHMS = [tempo_cpp.EnergyBPM, tempo_cpp.AutocorrBPM]


def _algo_id(cls) -> str:
    return cls.__name__


@pytest.mark.parametrize("algo_cls", ALGORITHMS, ids=_algo_id)
@pytest.mark.parametrize("bpm", [90.0, 120.0, 140.0])
@pytest.mark.parametrize("block_size", [48, 1024])
def test_detects_click_track_tempo(algo_cls, bpm, block_size):
    audio, sr = generate_click_track(bpm=bpm, duration_sec=20.0)
    run = simulate_realtime(algo_cls(), audio, sr, block_size)
    assert run.final_bpm == pytest.approx(bpm, abs=3.0)


@pytest.mark.parametrize("algo_cls", ALGORITHMS, ids=_algo_id)
def test_estimate_is_available_while_streaming(algo_cls):
    audio, sr = generate_click_track(bpm=120.0, duration_sec=12.0)
    run = simulate_realtime(algo_cls(), audio, sr, block_size=256)
    first_estimate_sec = next(
        t for t, bpm in zip(run.times_sec, run.bpm_estimates) if bpm > 0
    )
    assert first_estimate_sec < 5.0


@pytest.mark.parametrize("algo_cls", ALGORITHMS, ids=_algo_id)
def test_reset_clears_estimate(algo_cls):
    audio, sr = generate_click_track(bpm=120.0, duration_sec=10.0)
    algo = algo_cls()
    algo.reset(float(sr))
    algo.process_block(audio)
    assert algo.get_bpm() > 0.0

    algo.reset(float(sr))
    assert algo.get_bpm() == 0.0


@pytest.mark.parametrize("algo_cls", ALGORITHMS, ids=_algo_id)
def test_rejects_multidimensional_input(algo_cls):
    algo = algo_cls()
    algo.reset(22050.0)
    with pytest.raises(RuntimeError):
        algo.process_block(np.zeros((2, 64), dtype=np.float32))
