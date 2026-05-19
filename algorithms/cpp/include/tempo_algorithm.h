// algorithms/cpp/include/tempo_algorithm.h
//
// Базовый интерфейс для реалтайм-алгоритма определения темпа (BPM).
// Все алгоритмы наследуются от этого класса. Это позволяет:
//   - единообразно вызывать их из Python (через один pybind11 шаблон)
//   - легко добавлять новые алгоритмы
//   - использовать те же исходники в проекте DaisySeed без переписывания
//
#pragma once

#include <cstddef>

namespace tempo {

class TempoAlgorithm {
public:
    virtual ~TempoAlgorithm() = default;

    /// Сброс состояния алгоритма под заданную частоту дискретизации.
    /// Вызывается один раз перед началом потоковой обработки.
    virtual void reset(float sample_rate) = 0;

    /// Обработать блок моно-сэмплов в диапазоне [-1, 1].
    /// На DaisySeed сюда передаётся ровно один callback-блок (типично 48..1024 семплов).
    virtual void process_block(const float* samples, std::size_t num_samples) = 0;

    /// Текущая оценка темпа в BPM (0, если ещё не оценен).
    /// Может вызываться сколь угодно часто — должна быть дешёвой.
    virtual float get_bpm() const = 0;

    /// Имя алгоритма для отчётов/UI.
    virtual const char* name() const = 0;
};

} // namespace tempo
