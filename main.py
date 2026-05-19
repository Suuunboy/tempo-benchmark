"""CLI-скрипт стенда 

Примеры использования:

  # Запуск с дефолтным синтетическим клик-треком (120 BPM, 12 с)
  python main.py

  # Свой синтетический BPM/длительность (хорошо для регрессионного теста)
  python main.py --bpm 140 --duration 20

  # Загрузить свой аудио-файл
  python main.py --file path/to/song.mp3

  # Конкретные алгоритмы
  python main.py --algorithms energy_cpp,librosa_reference

  # Другой размер блока (как на DaisySeed - 48 или 256)
  python main.py --block-size 256

  # Без открытия окна matplotlib, только сохранение PNG
  python main.py --no-show --output results/run_001.png

  # Просто показать список зарегистрированных алгоритмов
  python main.py --list
"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys

from src import registry
from src.audio_io import generate_click_track, load_audio, DEFAULT_SR
from src.benchmark import run_benchmark
from src.visualization import plot_comparison


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Тестовый стенд для сравнения алгоритмов определения темпа музыки",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--file", type=str, default=None,
                    help="Путь к аудио-файлу. Если не указан, используется синтетический клик-трек.")
    p.add_argument("--bpm", type=float, default=120.0,
                    help="BPM для синтетического сигнала (если --file не задан)")
    p.add_argument("--duration", type=float, default=12.0,
                    help="Длительность синтетического сигнала, с")
    p.add_argument("--noise", type=float, default=0.0,
                    help="Уровень белого шума в синтетическом сигнале (0..1)")
    p.add_argument("--sample-rate", type=int, default=DEFAULT_SR,
                    help="Целевая частота дискретизации")
    p.add_argument("--block-size", type=int, default=1024,
                    help="Размер блока обработки (имитирует callback на DaisySeed)")
    p.add_argument("--algorithms", type=str, default=None,
                    help="Список ключей через запятую (пусто = все доступные)")
    p.add_argument("--output", type=str, default="results/comparison.png",
                    help="Путь сохранения PNG-отчёта")
    p.add_argument("--no-show", action="store_true",
                    help="Не открывать окно matplotlib")
    p.add_argument("--list", action="store_true",
                    help="Показать список зарегистрированных алгоритмов и выйти")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    registry.register_default_algorithms()

    if args.list:
        print("Доступные алгоритмы:")
        for k in registry.list_algorithms():
            print(f"  - {k}")
        return 0

    # 1. Загрузка / генерация аудио
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Файл не найден: {path}", file=sys.stderr)
            return 1
        print(f"Загрузка аудио: {path}")
        audio, sr = load_audio(str(path), target_sr=args.sample_rate)
        print(f"  длительность: {len(audio) / sr:.1f} с, частота: {sr} Hz")
        expected_bpm = None
    else:
        print(f"Использую синтетический клик-трек: {args.bpm:.1f} BPM, "
               f"{args.duration:.1f} с, шум={args.noise}")
        audio, sr = generate_click_track(
            bpm=args.bpm,
            duration_sec=args.duration,
            sample_rate=args.sample_rate,
            noise_level=args.noise,
        )
        expected_bpm = args.bpm

    # 2. Выбор алгоритмов
    available = registry.list_algorithms()
    if args.algorithms:
        keys = [k.strip() for k in args.algorithms.split(",") if k.strip()]
        unknown = [k for k in keys if k not in available]
        if unknown:
            print(f"Неизвестные алгоритмы: {unknown}", file=sys.stderr)
            print(f"Доступные: {available}", file=sys.stderr)
            return 1
    else:
        keys = available

    # 3. Прогон
    print(f"\nЗапуск бенчмарка ({len(keys)} алгоритм(ов), block_size={args.block_size}):")
    result = run_benchmark(audio, sr, keys, block_size=args.block_size)

    # 4. Печать сводки
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    if expected_bpm is not None:
        print(f"Истинный BPM (синтетика): {expected_bpm:.2f}")
    if result.reference_bpm is not None:
        print(f"Референсный BPM (librosa): {result.reference_bpm:.2f}")
    print()
    print(f"{'Алгоритм':<28} {'BPM':>8} {'Ошибка':>10} {'RT-фактор':>12}")
    print("-" * 62)
    errors = result.errors()
    for key, run in result.runs.items():
        err = errors.get(key)
        err_str = f"{err:+.2f}" if err is not None else "—"
        print(f"{run.algo_name:<28} {run.final_bpm:>8.2f} "
               f"{err_str:>10} {run.realtime_factor:>10.1f}x")
    print()

    # 5. Визуализация
    plot_comparison(audio, sr, result,
                     output_path=Path(args.output),
                     show=not args.no_show)
    return 0


if __name__ == "__main__":
    sys.exit(main())
