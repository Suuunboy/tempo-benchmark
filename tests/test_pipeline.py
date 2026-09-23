import numpy as np
import pytest

import main
from src import registry
from src.audio_io import generate_click_track
from src.benchmark import run_benchmark


def test_click_track_shape():
    audio, sr = generate_click_track(bpm=120.0, duration_sec=3.0, sample_rate=8000)
    assert sr == 8000
    assert audio.dtype == np.float32
    assert len(audio) == 3 * 8000


def test_default_algorithms_are_registered():
    registry.register_default_algorithms()
    assert {"librosa_reference", "energy_cpp", "autocorr_cpp"} <= set(
        registry.list_algorithms()
    )


def test_benchmark_uses_librosa_as_reference():
    registry.register_default_algorithms()
    audio, sr = generate_click_track(bpm=120.0, duration_sec=12.0)
    result = run_benchmark(audio, sr, registry.list_algorithms())

    assert result.reference_bpm == pytest.approx(120.0, abs=5.0)
    assert result.errors()["librosa_reference"] == 0.0
    for run in result.runs.values():
        assert run.final_bpm == pytest.approx(120.0, abs=5.0)
    # librosa's first call includes numba JIT warm-up, so only the C++
    # algorithms have a stable enough speed to assert on.
    for key in ("energy_cpp", "autocorr_cpp"):
        assert result.runs[key].realtime_factor > 1.0


def test_cli_writes_report(tmp_path, capsys):
    output = tmp_path / "report.png"
    exit_code = main.main(["--no-show", "--duration", "8", "--output", str(output)])

    assert exit_code == 0
    assert output.stat().st_size > 0
    assert "SUMMARY" in capsys.readouterr().out


def test_cli_lists_algorithms(capsys):
    assert main.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "energy_cpp" in out
    assert "autocorr_cpp" in out


def test_cli_rejects_unknown_algorithm(capsys):
    assert main.main(["--no-show", "--algorithms", "no_such_algo"]) == 1
    assert "Unknown algorithms" in capsys.readouterr().err
