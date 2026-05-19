// algorithms/cpp/bindings/python_bindings.cpp
//
// pybind11-биндинги для модуля tempo_cpp.
//
// Чтобы добавить новый алгоритм:
//   1) include его header
//   2) добавить блок py::class_<...> ниже (по примеру существующих)
//   3) добавить .cpp в setup.py
//   4) зарегистрировать в src/registry.py
//
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "tempo_algorithm.h"
#include "energy_bpm.h"
#include "autocorr_bpm.h"

namespace py = pybind11;
using namespace tempo;

// Обёртка: принимает numpy float32 массив и зовёт process_block с raw pointer
template <typename Algo>
static void process_numpy(Algo& self,
                          py::array_t<float, py::array::c_style | py::array::forcecast> arr) {
    py::buffer_info buf = arr.request();
    if (buf.ndim != 1) {
        throw std::runtime_error("Ожидается одномерный float32 массив");
    }
    const float* data = static_cast<const float*>(buf.ptr);
    self.process_block(data, static_cast<std::size_t>(buf.size));
}

PYBIND11_MODULE(tempo_cpp, m) {
    m.doc() = "Real-time BPM detection algorithms (C++ backend for tempo_benchmark)";

    // Базовый класс (нужен для наследования при py::class_)
    py::class_<TempoAlgorithm>(m, "TempoAlgorithm")
        .def("reset", &TempoAlgorithm::reset, py::arg("sample_rate"))
        .def("get_bpm", &TempoAlgorithm::get_bpm)
        .def_property_readonly("name", &TempoAlgorithm::name);

    py::class_<EnergyBPM, TempoAlgorithm>(m, "EnergyBPM")
        .def(py::init<float, float, float>(),
             py::arg("min_bpm")     = 60.0f,
             py::arg("max_bpm")     = 200.0f,
             py::arg("threshold_k") = 1.4f)
        .def("process_block", &process_numpy<EnergyBPM>, py::arg("samples"));

    py::class_<AutocorrBPM, TempoAlgorithm>(m, "AutocorrBPM")
        .def(py::init<float, float>(),
             py::arg("min_bpm") = 60.0f,
             py::arg("max_bpm") = 200.0f)
        .def("process_block", &process_numpy<AutocorrBPM>, py::arg("samples"));
}
