from __future__ import annotations
from typing import Callable, Dict, List

_registry: Dict[str, Callable] = {}


def register(key: str, factory: Callable) -> None:
    _registry[key] = factory


def list_algorithms() -> List[str]:
    return list(_registry.keys())


def create(key: str):
    if key not in _registry:
        raise KeyError(
            f"Алгоритм {key} не зарегистрирован. Доступные: {list_algorithms()}"
        )


def register_default_algorithms() -> None:
    from algorithms.python.reference_librosa import LibrosaReference

    register("librosa_reference", LibrosaReference)

    try:
        import tempo_cpp

        register("energy_cpp", lambda: tempo_cpp.EnergyBPM())
        register("autocorr_cpp", lambda: tempo_cpp.AutocorrBPM())

    except ImportError as e:
        print(f"[ВНИМАНИЕ] C++ модуль tempo_cpp не найден: {e}")
        print("          Соберите его командой: pip install -e .")
