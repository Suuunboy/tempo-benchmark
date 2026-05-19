"""Графики и инфографика сравнения алгоритмов.

Генерирует единый PNG-отчёт:
  - осциллограмма входного аудио
  - оценка BPM во времени для каждого алгоритма (видна скорость сходимости)
  - столбчатая диаграмма финальных оценок BPM с референс-линией
  - сравнение realtime-факторов (логарифмическая шкала)
  - сводная таблица
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import numpy as np

from src.benchmark import BenchmarkResult


def plot_comparison(
    audio: np.ndarray,
    sample_rate: int,
    result: BenchmarkResult,
    output_path: Optional[Path] = None,
    show: bool = True,
) -> None:
    """Построить и (опционально) сохранить полный отчёт."""
    import matplotlib.pyplot as plt
    import matplotlib

    # Нормальный шрифт для кириллицы (на большинстве систем DejaVu есть всегда)
    matplotlib.rcParams["font.family"] = "DejaVu Sans"

    n_algos = len(result.runs)
    fig = plt.figure(figsize=(14, 4 + 1.8 * n_algos + 4.5))
    height_ratios = [1.2] + [1.0] * n_algos + [1.4, 1.5]
    gs = fig.add_gridspec(
        n_algos + 3, 2, height_ratios=height_ratios, hspace=0.55, wspace=0.25
    )

    colors = plt.cm.tab10.colors

    # 1) Осциллограмма
    ax_wave = fig.add_subplot(gs[0, :])
    t = np.arange(len(audio)) / sample_rate
    ax_wave.plot(t, audio, color="#1f77b4", linewidth=0.5)
    ax_wave.set_title(
        f"Аудиосигнал ({result.audio_duration_sec:.1f} с, {sample_rate} Hz, "
        f"размер блока {result.block_size} сэмплов)",
        fontsize=11,
    )
    ax_wave.set_xlabel("Время, с")
    ax_wave.set_ylabel("Амплитуда")
    ax_wave.set_xlim(0, result.audio_duration_sec)
    ax_wave.grid(alpha=0.3)

    # 2) BPM во времени для каждого алгоритма (отдельный subplot)
    for i, (key, run) in enumerate(result.runs.items()):
        ax = fig.add_subplot(gs[i + 1, :])
        bpm_arr = np.array(run.bpm_estimates)
        time_arr = np.array(run.times_sec)
        mask = bpm_arr > 0

        # Эвристика: offline-алгоритм даёт результат только в конце.
        # У них значимая оценка появляется только в последней (1-2) точке(ах).
        is_offline = int(mask.sum()) <= 2 and len(bpm_arr) > 10
        color = colors[i % len(colors)]

        if is_offline:
            # Рисуем как горизонтальную линию по всей длительности
            # (значение известно только постфактум)
            ax.axhline(
                run.final_bpm,
                color=color,
                linewidth=2.0,
                linestyle="-",
                label=f"{run.algo_name}: {run.final_bpm:.1f} BPM (offline)",
            )
            ax.text(
                result.audio_duration_sec * 0.5,
                run.final_bpm + 5,
                "доступно только после окончания записи",
                fontsize=9,
                color=color,
                ha="center",
                style="italic",
            )
        else:
            ax.plot(
                time_arr[mask],
                bpm_arr[mask],
                color=color,
                linewidth=1.6,
                label=f"{run.algo_name}: финальный {run.final_bpm:.1f} BPM",
            )

        if result.reference_bpm is not None and not is_offline:
            ax.axhline(
                result.reference_bpm,
                color="red",
                linestyle="--",
                alpha=0.6,
                label=f"Референс: {result.reference_bpm:.1f} BPM",
            )

        ax.set_ylabel("BPM")
        ax.set_xlim(0, result.audio_duration_sec)
        ax.set_ylim(40, 220)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=9)
        if i == n_algos - 1:
            ax.set_xlabel("Время, с")

    # 3) Столбчатая диаграмма финальных BPM
    ax_bar = fig.add_subplot(gs[n_algos + 1, 0])
    names = [run.algo_name for run in result.runs.values()]
    bpms = [run.final_bpm for run in result.runs.values()]
    bars = ax_bar.barh(
        names, bpms, color=[colors[i % len(colors)] for i in range(len(names))]
    )
    if result.reference_bpm is not None:
        ax_bar.axvline(
            result.reference_bpm,
            color="red",
            linestyle="--",
            alpha=0.7,
            label=f"Референс: {result.reference_bpm:.1f}",
        )
        ax_bar.legend(fontsize=9)
    ax_bar.set_xlabel("BPM")
    ax_bar.set_title("Финальная оценка BPM", fontsize=11)
    ax_bar.grid(axis="x", alpha=0.3)
    # Расширяем правую границу, чтобы подписи помещались
    max_bpm = max(bpms) if bpms else 100.0
    if result.reference_bpm is not None:
        max_bpm = max(max_bpm, result.reference_bpm)
    ax_bar.set_xlim(0, max_bpm * 1.18)
    for bar, val in zip(bars, bpms):
        ax_bar.text(
            val + max_bpm * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}",
            va="center",
            fontsize=9,
        )

    # 4) Realtime-фактор
    ax_rt = fig.add_subplot(gs[n_algos + 1, 1])
    rt_factors = [max(run.realtime_factor, 0.01) for run in result.runs.values()]
    bars = ax_rt.barh(
        names, rt_factors, color=[colors[i % len(colors)] for i in range(len(names))]
    )
    ax_rt.axvline(1.0, color="red", linestyle="--", alpha=0.7, label="Real-time (1x)")
    ax_rt.set_xlabel("Realtime-фактор (длит. аудио / время обработки)")
    ax_rt.set_title("Скорость обработки", fontsize=11)
    ax_rt.set_xscale("log")
    # Расширяем правую границу под подписи в логарифмической шкале
    max_rt = max(rt_factors) if rt_factors else 1.0
    min_rt = min(rt_factors) if rt_factors else 0.01
    ax_rt.set_xlim(min_rt * 0.5, max_rt * 3.0)
    ax_rt.legend(fontsize=9)
    ax_rt.grid(axis="x", alpha=0.3, which="both")
    for bar, val in zip(bars, rt_factors):
        ax_rt.text(
            val * 1.1,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}x",
            va="center",
            fontsize=9,
        )

    # 5) Сводная таблица
    ax_table = fig.add_subplot(gs[n_algos + 2, :])
    ax_table.axis("off")

    headers = [
        "Алгоритм",
        "Финальный BPM",
        "Ошибка vs реф.",
        "Время обработки, с",
        "RT-фактор",
    ]
    rows = []
    errors = result.errors()
    for key, run in result.runs.items():
        err = errors.get(key)
        err_str = f"{err:+.2f}" if err is not None else "—"
        rows.append(
            [
                run.algo_name,
                f"{run.final_bpm:.2f}",
                err_str,
                f"{run.processing_time_sec:.3f}",
                f"{run.realtime_factor:.1f}x",
            ]
        )

    table = ax_table.table(
        cellText=rows,
        colLabels=headers,
        loc="center",
        cellLoc="center",
        colColours=["#cccccc"] * 5,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.7)

    fig.suptitle(
        "Сравнение алгоритмов определения BPM в реальном времени",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=120, bbox_inches="tight")
        print(f"\nГрафик сохранён: {output_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)
