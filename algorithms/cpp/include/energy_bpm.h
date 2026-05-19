// algorithms/cpp/include/energy_bpm.h
//
// EnergyBPM - реалтайм-детектор BPM по пикам энергии.
//
// Основан на классическом подходе (см. Scheirer 1998, Patin):
//   1. Поток сэмплов делится на короткие окна ~23 мс
//   2. В каждом окне считается средняя энергия (сумма квадратов / N)
//   3. Ведётся скользящая история ~1 секунды (43 окна)
//   4. Адаптивный порог = mean(history) + k * stddev(history)
//   5. Если текущая энергия > порога и прошло >= min_gap от последнего бита - это бит
//   6. BPM = медиана из последних оценок (по интервалам между битами)
//
// Достоинства: O(1) на сэмпл, минимум памяти (~200 байт состояния),
//              не требует FFT - идеально для Cortex-M7.
// Ограничения: лучше работает на перкуссивной музыке, слаб на legato/струнных.
//
#pragma once

#include "tempo_algorithm.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace tempo {

class EnergyBPM : public TempoAlgorithm {
public:
    explicit EnergyBPM(float min_bpm     = 60.0f,
                       float max_bpm     = 200.0f,
                       float threshold_k = 1.4f);

    void reset(float sample_rate) override;
    void process_block(const float* samples, std::size_t num_samples) override;
    float get_bpm() const override { return current_bpm_; }
    const char* name() const override { return "EnergyBPM (C++)"; }

private:
    void close_window();
    void register_beat(std::int64_t at_sample);

    // Параметры
    float min_bpm_;
    float max_bpm_;
    float threshold_k_;

    // Текущее окно интеграции энергии
    float sample_rate_{0.0f};
    std::size_t window_size_{0};
    std::size_t window_pos_{0};
    float window_energy_acc_{0.0f};

    // Кольцевой буфер истории энергии (~1 секунда)
    static constexpr std::size_t HISTORY_SIZE = 43;
    std::array<float, HISTORY_SIZE> energy_history_{};
    std::size_t history_idx_{0};
    std::size_t history_count_{0};

    // Учёт интервалов между битами
    std::int64_t samples_processed_{0};
    std::int64_t last_beat_sample_{-1};
    std::int64_t min_beat_gap_samples_{0};

    // Скользящее окно оценок BPM для медианной фильтрации
    static constexpr std::size_t MAX_INTERVALS = 24;
    std::array<float, MAX_INTERVALS> recent_bpms_{};
    std::size_t bpms_idx_{0};
    std::size_t bpms_count_{0};

    float current_bpm_{0.0f};
};

} // namespace tempo
