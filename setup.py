"""Build script for the ``tempo_cpp`` C++ extension (pybind11).

Project metadata lives in pyproject.toml; this file only describes the
extension module. Build and install everything with:

    pip install -e .

After that ``import tempo_cpp`` works from Python.
"""

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


ext_modules = [
    Pybind11Extension(
        "tempo_cpp",
        sources=[
            "algorithms/cpp/src/energy_bpm.cpp",
            "algorithms/cpp/src/autocorr_bpm.cpp",
            "algorithms/cpp/bindings/python_bindings.cpp",
        ],
        include_dirs=["algorithms/cpp/include"],
        cxx_std=17,
        extra_compile_args=["-O2"],
    ),
]


setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
