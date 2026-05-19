// algorithms/cpp/include/autocorr_bpm.h
//
// AutocorrBPM - реалтайм-детектор BPM на основе автокорреляции огибающей энергии.
//
// Идея:
//   1. Аудио конвертируется в огибающую энергии (RMS в коротких окнах ~10 мс)
//      -> снижение частоты в ~440 раз (от 44.1 кГц до ~100 Гц)
//   2. Огибающая хранится в кольцевом буфере ~6 секунд
//   3. Каждые ~0.5 сек запускается автокорреляция для интервала лагов,
//      соответствующего BPM 60..200
//   4. Берётся лаг с максимумом ACF -> BPM = 60 * envelope_rate / lag
//   5. Финальная оценка - медиана последних 8 значений (стабилизация)
//
// Достоинства:  устойчивее на не-перкуссивной музыке, лучше передаёт
//               периодичность, не зависит от индивидуальных битов
// Стоимость:    O(N * L) автокорреляции каждые 0.5 с, где N ~ 600, L ~ 70.
//               На Cortex-M7 это около 40-50 тыс. операций раз в 0.5 с — приемлемо.
//
#pragma once

#include "tempo_algorithm.h"
#include <cstddef>
#include <cstdint>
#include <vector>

namespace tempo {

class AutocorrBPM : public TempoAlgorithm {
public:
    explicit AutocorrBPM(float min_bpm = 60.0f, float max_bpm = 200.0f);

    void reset(float sample_rate) override;
    void process_block(const float* samples, std::size_t num_samples) override;
    float get_bpm() const override { return current_bpm_; }
    const char* name() const override { return "AutocorrBPM (C++)"; }

private:
    void close_window();
    void compute_bpm();

    // Параметры
    float min_bpm_;
    float max_bpm_;

    // Окно интегрирования энергии (RMS)
    float sample_rate_{0.0f};
    std::size_t window_size_{0};
    std::size_t window_pos_{0};
    float window_energy_acc_{0.0f};
    float envelope_rate_{0.0f}; // частота отсчётов огибающей в Гц

    // Кольцевой буфер огибающей
    std::vector<float> envelope_;
    std::size_t envelope_size_{0};
    std::size_t envelope_idx_{0};
    std::size_t envelope_count_{0};

    // Когда пересчитывать BPM
    std::size_t windows_since_compute_{0};
    std::size_t compute_period_windows_{0};

    // Медианное сглаживание BPM
    static constexpr std::size_t SMOOTH_SIZE = 8;
    float bpm_history_[SMOOTH_SIZE]{};
    std::size_t bpm_history_idx_{0};
    std::size_t bpm_history_count_{0};

    float current_bpm_{0.0f};
};

} // namespace tempo
