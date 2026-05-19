"""setup.py — сборка C++ модуля tempo_cpp через pybind11.

Запуск:
    pip install -e .

После этого `import tempo_cpp` доступен из Python.
"""

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


ext_modules = [
    Pybind11Extension(
        "tempo_cpp",
        sources=[
            "algorithms/cpp/src/autocorr_bpm.cpp",
            "algorithms/cpp/bindings/python_bindings.cpp",
        ],
        include_dirs=["algorithms/cpp/include"],
        cxx_std=17,
        extra_compile_args=["-O2"],
    ),
]


setup(
    name="tempo_benchmark",
    version="0.1.0",
    description="Real-time BPM detection algorithms comparison testbench",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    packages=["src", "algorithms", "algorithms.python"],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",
        "scipy>=1.10",
        "librosa>=0.10.0",
        "soundfile>=0.12",
        "matplotlib>=3.7",
    ],
)
