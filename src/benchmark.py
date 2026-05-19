from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from src.simulator import RealtimeRun, simulate_realtime
from src import registry


@dataclass
class BenchmarkResult:
    audio_duration_sec: float
    sample_rate: int
    block_size: int
    reference_bpm: Optional[float] = None

    def errors(self) -> Dict[str, float]:
        """Подписная ошибка каждого алгоритма относительно референса"""
        if self.reference_bpm is None:
            return {}
        return {
            name: run.final_bpm - self.reference_bpm for name, run in self.runs.items()
        }


def run_benchmark(
    audio: np.ndarray,
    sample_rate: int,
    algorithm_keys: List[str],
    block_size: int = 1024,
    reference_key: str = "librosa_reference",
) -> BenchmarkResult:
    result = BenchmarkResult(
        audio_duration_sec=len(audio) / sample_rate,
        sample_rate=sample_rate,
        block_size=block_size,
    )

    for key in algorithm_keys:
        print(f"  > Запуск '{key}'...", end="", flush=True)
        algo = registry.create(key)
        run = simulate_realtime(algo, audio, sample_rate, block_size)
        result.run[key] = run
        print(
            f" BPM={run.final_bpm:6.2f}  "
            f"время={run.processing_time_sec:.2f}с  "
            f"(RT-фактор {run.realtime_factor:.1f}x)"
        )

    if reference_key in result.runs:
        result.reference_bpm = result.runs[reference_key].final_bpm

    return result
