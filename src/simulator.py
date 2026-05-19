from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import time

import numpy as np


@dataclass
class RealtimeRun:
    """Результат одного прохода алгоритма в режиме реального времени."""

    algo_name: str
    block_size: int
    sample_rate: int
    times_sec: List[float] = field(default_factory=list)
    bpm_estimates: List[float] = field(default_factory=list)
    processing_time_sec: float = 0.0
    final_bpm: float = 0.0
    audio_duration_sec: float = 0.0

    @property
    def realtime_factor(self) -> float:
        """Отношение длительности аудио к времени обработки.

        > 1: алгоритм быстрее реального времени
        = 1: ровно в реальном времени
        < 1: не успевает
        """
        if self.processing_time_sec <= 0:
            return float("inf")
        return self.audio_duration_sec / self.processing_time_sec


def simulate_realtime(
    algorithm, audio: np.ndarray, sample_rate: int, block_size: int = 1024
) -> RealtimeRun:
    """Прогнать алгоритм по аудио блоками. Возвращает динамику оценок BPM."""

    name = getattr(algorithm, "name", algorithm.__class__.__name__)
    algorithm.reset(float(sample_rate))

    run = RealtimeRun(
        algo_name=name,
        block_size=block_size,
        sample_rate=sample_rate,
        audio_duration_sec=len(audio) / sample_rate,
    )

    n_samples = len(audio)
    n_blocks = (n_samples + block_size - 1) // block_size

    t_start = time.perf_counter()
    for b in range(n_blocks):
        start = b * block_size
        end = min(start + block_size, n_samples)
        block = audio[start:end].astype(np.float32, copy=False)
        # Гарантируем contiguous буфер — pybind11 будет читать как float*
        if not block.flags.c_contiguous:
            block = np.ascontiguousarray(block)

        algorithm.process_block(block)

        # Записываем текущую оценку в момент конца блока
        t_in_track = end / sample_rate
        bpm = algorithm.get_bpm()
        run.times_sec.append(t_in_track)
        run.bpm_estimates.append(bpm)

    # Для offline-алгоритмов (librosa) - финальный расчёт.
    # Оценка появляется только в самом конце, поэтому ставим её только
    # в последнюю точку, остальные оставляем нулями — это честнее отражает
    # тот факт, что offline-алгоритм не работает в реальном времени.
    if hasattr(algorithm, "finalize"):
        bpm_final = algorithm.finalize()
        if run.bpm_estimates:
            run.bpm_estimates[-1] = bpm_final

    run.processing_time_sec = time.perf_counter() - t_start
    run.final_bpm = algorithm.get_bpm()
    return run
