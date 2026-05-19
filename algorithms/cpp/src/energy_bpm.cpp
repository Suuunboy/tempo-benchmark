// algorithms/cpp/src/energy_bpm.cpp
#include "energy_bpm.h"

#include <algorithm>
#include <cmath>

namespace tempo {

EnergyBPM::EnergyBPM(float min_bpm, float max_bpm, float threshold_k)
    : min_bpm_(min_bpm), max_bpm_(max_bpm), threshold_k_(threshold_k) {}

void EnergyBPM::reset(float sample_rate) {
    sample_rate_ = sample_rate;

    // Окно интегрирования энергии ~23 мс. Типично 1024 семпла @ 44.1 кГц.
    // Это компромисс между разрешением и стабильностью оценки энергии.
    window_size_ = static_cast<std::size_t>(sample_rate_ * 0.023f);
    if (window_size_ < 32) window_size_ = 32;

    window_pos_         = 0;
    window_energy_acc_  = 0.0f;

    energy_history_.fill(0.0f);
    history_idx_   = 0;
    history_count_ = 0;

    samples_processed_     = 0;
    last_beat_sample_      = -1;
    // Минимальный интервал между битами = 60/max_bpm секунд
    min_beat_gap_samples_  = static_cast<std::int64_t>(sample_rate_ * 60.0f / max_bpm_);

    recent_bpms_.fill(0.0f);
    bpms_idx_   = 0;
    bpms_count_ = 0;

    current_bpm_ = 0.0f;
}

void EnergyBPM::close_window() {
    const float energy = window_energy_acc_ / static_cast<float>(window_size_);

    // Считаем среднее и СКО по истории
    float mean = 0.0f;
    for (std::size_t i = 0; i < history_count_; ++i) mean += energy_history_[i];
    if (history_count_ > 0) mean /= static_cast<float>(history_count_);

    float var = 0.0f;
    for (std::size_t i = 0; i < history_count_; ++i) {
        const float d = energy_history_[i] - mean;
        var += d * d;
    }
    if (history_count_ > 1) var /= static_cast<float>(history_count_ - 1);
    const float std_dev = std::sqrt(var);

    const float threshold = mean + threshold_k_ * std_dev;

    // Регистрируем бит, если набралась хотя бы половина истории и пик выше порога
    if (history_count_ >= HISTORY_SIZE / 2 &&
        energy > threshold && energy > 1e-7f) {
        const std::int64_t now = samples_processed_;
        if (last_beat_sample_ < 0 || (now - last_beat_sample_) > min_beat_gap_samples_) {
            register_beat(now);
        }
    }

    // Кольцевой push в историю
    energy_history_[history_idx_] = energy;
    history_idx_ = (history_idx_ + 1) % HISTORY_SIZE;
    if (history_count_ < HISTORY_SIZE) ++history_count_;

    window_energy_acc_ = 0.0f;
    window_pos_        = 0;
}

void EnergyBPM::register_beat(std::int64_t at_sample) {
    if (last_beat_sample_ >= 0) {
        const std::int64_t interval = at_sample - last_beat_sample_;
        const float interval_sec    = static_cast<float>(interval) / sample_rate_;
        float bpm = 60.0f / interval_sec;

        // Поправляем октавы: если попали в половинный/двойной темп, сдвинем в диапазон
        while (bpm > 0.0f && bpm < min_bpm_) bpm *= 2.0f;
        while (bpm > max_bpm_)               bpm *= 0.5f;

        if (bpm >= min_bpm_ && bpm <= max_bpm_) {
            recent_bpms_[bpms_idx_] = bpm;
            bpms_idx_ = (bpms_idx_ + 1) % MAX_INTERVALS;
            if (bpms_count_ < MAX_INTERVALS) ++bpms_count_;

            // Медианная фильтрация оценок — устойчива к выбросам
            if (bpms_count_ >= 4) {
                float sorted[MAX_INTERVALS];
                for (std::size_t i = 0; i < bpms_count_; ++i) sorted[i] = recent_bpms_[i];
                std::sort(sorted, sorted + bpms_count_);
                current_bpm_ = sorted[bpms_count_ / 2];
            }
        }
    }
    last_beat_sample_ = at_sample;
}

void EnergyBPM::process_block(const float* samples, std::size_t num_samples) {
    for (std::size_t i = 0; i < num_samples; ++i) {
        const float s = samples[i];
        window_energy_acc_ += s * s;
        ++window_pos_;
        ++samples_processed_;

        if (window_pos_ >= window_size_) {
            close_window();
        }
    }
}

} // namespace tempo
